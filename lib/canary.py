"""Canary prompts, stored responses, and skill-trend computation.

The canary system is the Forge Protocol's measurable-skill mechanism:
the user answers a *fixed* set of prompts unassisted, we score each
attempt with the adversarial auditor (Claude Sonnet), and compare scores
across time to detect whether the user's independent skills are drifting
up or down.

Storage is a single JSON file at ``$FORGE_STATE_DIR/canary_history.json``
(default ``~/.forge-state/canary_history.json``). Keyed by prompt id, each
value is a list of attempts sorted oldest-first.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from . import auditor


# ---------------------------------------------------------------------------
# Canary question bank — stable IDs so we can track trend per-prompt.
# ---------------------------------------------------------------------------

CANARY_QUESTIONS: list[dict[str, Any]] = [
    {
        "id": "writing_email_decline",
        "category": "writing",
        "prompt": "Write a 150-word professional email declining a meeting invitation while maintaining the relationship.",
        "time_limit_minutes": 5,
    },
    {
        "id": "analysis_failure_modes",
        "category": "analysis",
        "prompt": "Identify three potential failure modes of a system you work on. For each, explain the root cause and one mitigation.",
        "time_limit_minutes": 10,
    },
    {
        "id": "debugging_mental_model",
        "category": "debugging",
        "prompt": "Describe your mental model for debugging a production issue. What are the first 5 things you check, and why in that order?",
        "time_limit_minutes": 8,
    },
    {
        "id": "strategy_prioritization",
        "category": "strategy",
        "prompt": "Your team has twice as much work as capacity for the next quarter. Write a prioritization framework in 200 words.",
        "time_limit_minutes": 10,
    },
    {
        "id": "communication_tech_decision",
        "category": "communication",
        "prompt": "Write a brief message explaining a complex technical decision to a non-technical stakeholder. Topic: why a feature will be delayed.",
        "time_limit_minutes": 5,
    },
]


def list_canary_questions() -> list[dict[str, Any]]:
    """Return the full question bank (immutable copy of each entry)."""
    return [dict(q) for q in CANARY_QUESTIONS]


def get_canary_question_by_id(prompt_id: str) -> dict[str, Any] | None:
    for q in CANARY_QUESTIONS:
        if q["id"] == prompt_id:
            return dict(q)
    return None


# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------

def _default_state_dir() -> Path:
    env = os.environ.get("FORGE_STATE_DIR")
    return Path(env).expanduser() if env else Path.home() / ".forge-state"


@dataclass
class CanaryAttempt:
    timestamp: float
    prompt_id: str
    response: str
    overall: float
    dimensions: dict[str, int] = field(default_factory=dict)
    notes: str = ""
    auditor_model: str = ""
    error: str | None = None


@dataclass
class CanaryTrend:
    prompt_id: str
    attempts: int
    last_score: float | None
    prev_score: float | None
    change_vs_prev: float | None
    mean_last_5: float | None
    slope_per_attempt: float | None   # linear regression slope over attempt index
    history: list[dict[str, Any]] = field(default_factory=list)


class CanaryStore:
    """Cross-session store of canary attempts."""

    def __init__(self, state_dir: str | Path | None = None):
        self.state_dir = Path(state_dir).expanduser() if state_dir else _default_state_dir()
        self.path = self.state_dir / "canary_history.json"

    def _load(self) -> dict[str, list[dict[str, Any]]]:
        if not self.path.exists():
            return {}
        with open(self.path, encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}

    def _save(self, data: dict[str, list[dict[str, Any]]]) -> None:
        self.state_dir.mkdir(parents=True, exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def record(self, attempt: CanaryAttempt) -> None:
        data = self._load()
        data.setdefault(attempt.prompt_id, []).append(asdict(attempt))
        # keep oldest-first; append is already correct if calls are chronological
        data[attempt.prompt_id].sort(key=lambda a: a["timestamp"])
        self._save(data)

    def get_attempts(self, prompt_id: str) -> list[CanaryAttempt]:
        data = self._load()
        raw = data.get(prompt_id, [])
        return [CanaryAttempt(**a) for a in raw]


# ---------------------------------------------------------------------------
# Scoring + trend
# ---------------------------------------------------------------------------

def _linreg_slope(ys: list[float]) -> float | None:
    """Linear regression slope of y over index x = 0..n-1. None if <2 points."""
    n = len(ys)
    if n < 2:
        return None
    xs = list(range(n))
    mean_x = sum(xs) / n
    mean_y = sum(ys) / n
    num = sum((xs[i] - mean_x) * (ys[i] - mean_y) for i in range(n))
    den = sum((xs[i] - mean_x) ** 2 for i in range(n))
    if den == 0:
        return None
    return round(num / den, 3)


def compute_trend(prompt_id: str, store: CanaryStore | None = None) -> CanaryTrend:
    store = store or CanaryStore()
    attempts = store.get_attempts(prompt_id)
    scored = [a for a in attempts if a.overall > 0 and a.error is None]
    history = [
        {"timestamp": a.timestamp, "overall": a.overall, "dimensions": a.dimensions}
        for a in attempts
    ]
    if not scored:
        return CanaryTrend(
            prompt_id=prompt_id,
            attempts=len(attempts),
            last_score=None,
            prev_score=None,
            change_vs_prev=None,
            mean_last_5=None,
            slope_per_attempt=None,
            history=history,
        )
    overalls = [a.overall for a in scored]
    last = overalls[-1]
    prev = overalls[-2] if len(overalls) >= 2 else None
    change = round(last - prev, 2) if prev is not None else None
    mean_last_5 = round(sum(overalls[-5:]) / min(len(overalls), 5), 2)
    return CanaryTrend(
        prompt_id=prompt_id,
        attempts=len(attempts),
        last_score=last,
        prev_score=prev,
        change_vs_prev=change,
        mean_last_5=mean_last_5,
        slope_per_attempt=_linreg_slope(overalls),
        history=history,
    )


def submit_canary(
    prompt_id: str,
    response: str,
    *,
    store: CanaryStore | None = None,
    client: Any | None = None,
) -> tuple[CanaryAttempt, CanaryTrend]:
    """Score a user's unassisted response with the auditor, store it, return trend.

    If the auditor is disabled, the attempt is still stored (with overall=0 and
    error="auditor_disabled") so the response isn't lost — rescoring can be
    done later when the auditor is enabled.
    """
    question = get_canary_question_by_id(prompt_id)
    if question is None:
        raise ValueError(f"unknown canary prompt_id: {prompt_id!r}")

    store = store or CanaryStore()
    score = auditor.score_canary(question["prompt"], response, client=client)
    attempt = CanaryAttempt(
        timestamp=time.time(),
        prompt_id=prompt_id,
        response=response,
        overall=score.overall,
        dimensions=score.dimensions,
        notes=score.notes,
        auditor_model=score.auditor_model,
        error=score.error,
    )
    store.record(attempt)
    trend = compute_trend(prompt_id, store=store)
    return attempt, trend
