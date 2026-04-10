"""Self-audit system: weekly canary, monthly stress test, quarterly dependency audit."""

from __future__ import annotations

import random
import time
from dataclasses import dataclass, field

from .modes import VALID_MODE_IDS
from .state import Session, StateManager

# Time constants
DAY_SECONDS = 24 * 60 * 60
WEEK_SECONDS = 7 * DAY_SECONDS
MONTH_SECONDS = 30 * DAY_SECONDS
QUARTER_SECONDS = 90 * DAY_SECONDS


def _days_since(last: float | None, fallback: float, now: float) -> int:
    return int((now - (last or fallback)) / DAY_SECONDS)


@dataclass
class AuditReminder:
    audit_type: str  # "canary", "stress_test", "dependency"
    message: str
    overdue_days: int


@dataclass
class ModeRatios:
    forge: float = 0.0
    anvil: float = 0.0
    furnace: float = 0.0
    executor: float = 0.0


@dataclass
class DependencyReport:
    total_sessions: int = 0
    total_messages: int = 0
    mode_ratios: ModeRatios = field(default_factory=ModeRatios)
    total_violations: int = 0
    assessment: str = ""


def check_audit_reminders(session: Session) -> list[AuditReminder]:
    """Check which audits are overdue and return reminders."""
    now = time.time()
    reminders: list[AuditReminder] = []

    last_canary = session.audit_status.last_canary
    if last_canary is None or (now - last_canary) > WEEK_SECONDS:
        days_overdue = _days_since(last_canary, session.created_at, now)
        reminders.append(
            AuditReminder(
                audit_type="canary",
                message=(
                    f"Weekly canary check is {days_overdue} days overdue. "
                    "Run /forge-audit weekly to test your unassisted skills."
                ),
                overdue_days=days_overdue,
            )
        )

    last_stress = session.audit_status.last_stress_test
    if last_stress is None or (now - last_stress) > MONTH_SECONDS:
        days_overdue = _days_since(last_stress, session.created_at, now)
        if days_overdue > 30:
            reminders.append(
                AuditReminder(
                    audit_type="stress_test",
                    message=(
                        f"Monthly stress test is {days_overdue} days overdue. "
                        "Run /forge-audit monthly for a timed challenge without AI."
                    ),
                    overdue_days=days_overdue,
                )
            )

    last_dep = session.audit_status.last_dependency_audit
    if last_dep is None or (now - last_dep) > QUARTER_SECONDS:
        days_overdue = _days_since(last_dep, session.created_at, now)
        if days_overdue > 90:
            reminders.append(
                AuditReminder(
                    audit_type="dependency",
                    message=(
                        f"Quarterly dependency audit is {days_overdue} days overdue. "
                        "Run /forge-audit quarterly to review your AI usage patterns."
                    ),
                    overdue_days=days_overdue,
                )
            )

    return reminders


def compute_dependency_report(state_manager: StateManager) -> DependencyReport:
    """Analyze all sessions to compute mode usage ratios and dependency metrics."""
    session_ids = state_manager.list_sessions()
    if not session_ids:
        return DependencyReport(assessment="No sessions found.")

    total_messages = 0
    mode_messages = {m: 0 for m in VALID_MODE_IDS}
    total_violations = 0

    for sid in session_ids:
        session = state_manager.get_session(sid)
        if session is None:
            continue
        total_messages += session.message_count
        total_violations += len(session.violations)

        for entry in session.mode_history:
            mode = entry.mode
            if mode in mode_messages:
                mode_messages[mode] += entry.message_count

    if total_messages == 0:
        return DependencyReport(
            total_sessions=len(session_ids),
            assessment="No messages recorded yet.",
        )

    ratios = ModeRatios(
        forge=round(mode_messages["forge"] / total_messages, 2),
        anvil=round(mode_messages["anvil"] / total_messages, 2),
        furnace=round(mode_messages["furnace"] / total_messages, 2),
        executor=round(mode_messages["executor"] / total_messages, 2),
    )

    # Assess health
    thinking_ratio = ratios.forge + ratios.anvil + ratios.furnace
    if ratios.executor > 0.7:
        assessment = (
            f"WARNING: {ratios.executor:.0%} of interactions are in Executor mode. "
            "This suggests heavy delegation of thinking tasks. "
            "Target: ~40% Forge/Furnace, ~30% Anvil, ~30% Executor."
        )
    elif thinking_ratio > 0.5:
        assessment = (
            f"Healthy balance: {thinking_ratio:.0%} thinking modes, "
            f"{ratios.executor:.0%} executor. You're maintaining cognitive engagement."
        )
    else:
        assessment = (
            f"Mode split: Forge {ratios.forge:.0%}, Anvil {ratios.anvil:.0%}, "
            f"Furnace {ratios.furnace:.0%}, Executor {ratios.executor:.0%}."
        )

    return DependencyReport(
        total_sessions=len(session_ids),
        total_messages=total_messages,
        mode_ratios=ratios,
        total_violations=total_violations,
        assessment=assessment,
    )


# Canary check question bank
CANARY_QUESTIONS = [
    {
        "category": "writing",
        "prompt": "Write a 150-word professional email declining a meeting invitation while maintaining the relationship.",
        "time_limit_minutes": 5,
    },
    {
        "category": "analysis",
        "prompt": "Identify three potential failure modes of a system you work on. For each, explain the root cause and one mitigation.",
        "time_limit_minutes": 10,
    },
    {
        "category": "debugging",
        "prompt": "Describe your mental model for debugging a production issue. What are the first 5 things you check, and why in that order?",
        "time_limit_minutes": 8,
    },
    {
        "category": "strategy",
        "prompt": "Your team has twice as much work as capacity for the next quarter. Write a prioritization framework in 200 words.",
        "time_limit_minutes": 10,
    },
    {
        "category": "communication",
        "prompt": "Write a brief message explaining a complex technical decision to a non-technical stakeholder. Topic: why a feature will be delayed.",
        "time_limit_minutes": 5,
    },
]


def get_canary_question(category: str | None = None) -> dict:
    """Pick a random canary question, optionally filtered by category."""
    pool = CANARY_QUESTIONS
    if category:
        pool = [q for q in pool if q["category"] == category]
    if not pool:
        pool = CANARY_QUESTIONS
    return random.choice(pool)
