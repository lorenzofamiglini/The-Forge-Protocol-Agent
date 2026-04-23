"""Adversarial auditor — a second model evaluates compliance.

The Forge Protocol's original design asks the SAME orchestrator LLM that
produced a response to judge whether it complied with the mode's rules.
LLMs are poor at that kind of self-judgment; they readily rubber-stamp
their own work. This module fixes that by calling a *different* model
instance (Claude Sonnet by default) to audit compliance independently.

The auditor is OPTIONAL and opt-in. If disabled or the anthropic SDK is
not installed, the validator tools fall back to returning rules for the
orchestrator to self-evaluate (the original behavior).

Configuration via environment variables:

    FORGE_AUDITOR_ENABLED   "1" to enable (default: disabled)
    FORGE_AUDITOR_MODEL     Claude model id (default: claude-sonnet-4-6)
    FORGE_AUDITOR_BACKEND   "anthropic" | "vertex"   (default: anthropic)
    ANTHROPIC_API_KEY       Required for anthropic backend
    VERTEX_PROJECT          Required for vertex backend
    VERTEX_REGION           Optional, defaults to us-east5

Use the same variables for canary scoring — the auditor is shared.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .validator import InputRules, OutputRules


DEFAULT_MODEL = "claude-sonnet-4-6"
DEFAULT_BACKEND = "anthropic"
DEFAULT_VERTEX_REGION = "us-east5"
MAX_TOKENS = 1024


# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------

@dataclass
class RuleViolation:
    rule: str
    kind: str              # "required_missing" | "forbidden" | "input"
    quote: str = ""        # verbatim excerpt from the audited text, if any
    reason: str = ""       # one-line explanation


@dataclass
class AuditResult:
    compliant: bool
    violations: list[RuleViolation] = field(default_factory=list)
    auditor_model: str = ""
    raw_response: str = ""
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "compliant": self.compliant,
            "violations": [
                {"rule": v.rule, "kind": v.kind, "quote": v.quote, "reason": v.reason}
                for v in self.violations
            ],
            "auditor_model": self.auditor_model,
            "error": self.error,
        }


@dataclass
class CanaryScore:
    overall: float
    dimensions: dict[str, int] = field(default_factory=dict)
    notes: str = ""
    auditor_model: str = ""
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "overall": self.overall,
            "dimensions": self.dimensions,
            "notes": self.notes,
            "auditor_model": self.auditor_model,
            "error": self.error,
        }


# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------

_OUTPUT_AUDIT_SYSTEM = (
    "You are an adversarial auditor for the Forge Protocol. Your job is to "
    "evaluate whether an AI response complied with the behavioral rules of a "
    "given interaction mode. Be strict. If a response is close-but-not-quite, "
    "flag it. Cite specific text. Do not rubber-stamp because the response "
    "sounds reasonable — judge only against the rules."
)

_OUTPUT_AUDIT_USER_TEMPLATE = """\
MODE: {mode_name} ({mode_id})

REQUIRED BEHAVIORS (the response must demonstrate all of these):
{required}

FORBIDDEN BEHAVIORS (the response must do NONE of these):
{forbidden}

RESPONSE TO AUDIT:
---
{response}
---

Return strict JSON with this exact shape. No prose outside the JSON.

{{
  "compliant": true|false,
  "violations": [
    {{
      "rule": "<exact rule text that was violated>",
      "kind": "required_missing" | "forbidden",
      "quote": "<verbatim quote from the response, or empty for required_missing>",
      "reason": "<one-sentence explanation>"
    }}
  ]
}}

Rules for judgment:
- If a REQUIRED behavior is not clearly demonstrated, include it with kind="required_missing" and quote="".
- If a FORBIDDEN behavior is present, include it with kind="forbidden" and a verbatim quote.
- If fully compliant, return {{"compliant": true, "violations": []}}.
"""


_INPUT_AUDIT_SYSTEM = (
    "You are an adversarial auditor for the Forge Protocol. Evaluate whether a "
    "user's input meets the mode's entry requirements. In thinking modes, users "
    "must not fragment-dump or ask the AI to think for them. If the input is "
    "insufficient, flag which rule is unmet."
)

_INPUT_AUDIT_USER_TEMPLATE = """\
MODE: {mode_name} ({mode_id})

INPUT RULES (the user must satisfy all of these before the LLM engages):
{rules}

USER INPUT:
---
{user_input}
---

Return strict JSON. No prose outside the JSON.

{{
  "compliant": true|false,
  "violations": [
    {{
      "rule": "<exact rule text not met>",
      "kind": "input",
      "quote": "",
      "reason": "<one-sentence explanation of what's missing>"
    }}
  ]
}}

If every rule is met, return {{"compliant": true, "violations": []}}.
"""


_CANARY_SCORE_SYSTEM = (
    "You are a writing and reasoning evaluator. Score a user's unassisted "
    "response to a canary prompt on three dimensions (1-5 integers) and give "
    "one sentence of notes. Be honest — the user is using these scores to "
    "track whether their independent skills are improving or decaying over "
    "time, so flattery is counterproductive."
)

_CANARY_SCORE_USER_TEMPLATE = """\
CANARY PROMPT (the user was asked to answer this unassisted):
{prompt}

USER'S UNASSISTED RESPONSE:
---
{response}
---

Score the response on these dimensions, each 1 (poor) to 5 (excellent):
- clarity: specific, readable, no unnecessary hedging
- depth: shows genuine reasoning, not templated filler
- independence: reads like the user's own voice, not pasted AI output

Return strict JSON. No prose outside the JSON.

{{
  "dimensions": {{"clarity": <1-5>, "depth": <1-5>, "independence": <1-5>}},
  "notes": "<one sentence on the strongest or weakest aspect>"
}}
"""


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

def is_enabled() -> bool:
    return os.environ.get("FORGE_AUDITOR_ENABLED", "").lower() in ("1", "true", "yes", "on")


def model_name() -> str:
    return os.environ.get("FORGE_AUDITOR_MODEL", DEFAULT_MODEL)


def backend_name() -> str:
    return os.environ.get("FORGE_AUDITOR_BACKEND", DEFAULT_BACKEND).lower()


def _build_client() -> Any:
    backend = backend_name()
    try:
        if backend == "vertex":
            from anthropic import AnthropicVertex
            project = os.environ.get("VERTEX_PROJECT")
            if not project:
                raise RuntimeError("VERTEX_PROJECT not set for vertex auditor backend")
            region = os.environ.get("VERTEX_REGION", DEFAULT_VERTEX_REGION)
            return AnthropicVertex(project_id=project, region=region)
        from anthropic import Anthropic
        return Anthropic()
    except ImportError as e:
        raise RuntimeError(
            "anthropic SDK not installed. Run: pip install anthropic "
            "(or pip install 'forge-protocol[vertex]' for Vertex AI)"
        ) from e


# ---------------------------------------------------------------------------
# Low-level invoke helper
# ---------------------------------------------------------------------------

def _invoke(client: Any, system: str, user: str) -> str:
    msg = client.messages.create(
        model=model_name(),
        max_tokens=MAX_TOKENS,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    parts = msg.content or []
    for part in parts:
        text = getattr(part, "text", None)
        if text:
            return text
    return ""


def _extract_json(text: str) -> dict[str, Any]:
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError(f"no JSON object in auditor response: {text[:200]!r}")
    return json.loads(text[start : end + 1])


def _fmt_bullets(items: list[str]) -> str:
    return "\n".join(f"- {s}" for s in items) if items else "(none)"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def audit_output(
    response: str,
    rules: "OutputRules",
    *,
    client: Any | None = None,
) -> AuditResult | None:
    """Audit a response against a mode's output rules.

    Returns None if the auditor is disabled (caller should fall back to
    self-evaluation). Returns an AuditResult with ``error`` populated on
    backend/parse failure — by convention, audit errors do not block the
    response (``compliant`` defaults to True on error).
    """
    if not is_enabled():
        return None

    model = model_name()
    try:
        c = client if client is not None else _build_client()
        user = _OUTPUT_AUDIT_USER_TEMPLATE.format(
            mode_name=rules.mode_name,
            mode_id=rules.mode,
            required=_fmt_bullets(rules.required_behaviors),
            forbidden=_fmt_bullets(rules.forbidden_behaviors),
            response=response,
        )
        raw = _invoke(c, _OUTPUT_AUDIT_SYSTEM, user)
        parsed = _extract_json(raw)
        violations = [
            RuleViolation(
                rule=str(v.get("rule", "")),
                kind=str(v.get("kind", "forbidden")),
                quote=str(v.get("quote", "")),
                reason=str(v.get("reason", "")),
            )
            for v in parsed.get("violations", [])
        ]
        return AuditResult(
            compliant=bool(parsed.get("compliant", True)),
            violations=violations,
            auditor_model=model,
            raw_response=raw,
        )
    except Exception as e:  # noqa: BLE001 — auditor must never crash the tool
        return AuditResult(
            compliant=True,
            violations=[],
            auditor_model=model,
            raw_response="",
            error=f"{type(e).__name__}: {e}",
        )


def audit_input(
    user_input: str,
    rules: "InputRules",
    *,
    client: Any | None = None,
) -> AuditResult | None:
    """Audit a user input against a mode's input rules."""
    if not is_enabled():
        return None
    if not rules.rules:
        # nothing to check (executor mode, etc.)
        return AuditResult(compliant=True, auditor_model=model_name())

    model = model_name()
    try:
        c = client if client is not None else _build_client()
        user = _INPUT_AUDIT_USER_TEMPLATE.format(
            mode_name=rules.mode_name,
            mode_id=rules.mode,
            rules=_fmt_bullets(rules.rules),
            user_input=user_input,
        )
        raw = _invoke(c, _INPUT_AUDIT_SYSTEM, user)
        parsed = _extract_json(raw)
        violations = [
            RuleViolation(
                rule=str(v.get("rule", "")),
                kind="input",
                quote=str(v.get("quote", "")),
                reason=str(v.get("reason", "")),
            )
            for v in parsed.get("violations", [])
        ]
        return AuditResult(
            compliant=bool(parsed.get("compliant", True)),
            violations=violations,
            auditor_model=model,
            raw_response=raw,
        )
    except Exception as e:  # noqa: BLE001
        return AuditResult(
            compliant=True,
            violations=[],
            auditor_model=model,
            raw_response="",
            error=f"{type(e).__name__}: {e}",
        )


def score_canary(
    prompt: str,
    response: str,
    *,
    client: Any | None = None,
) -> CanaryScore:
    """Score a user's unassisted canary response on clarity, depth, independence.

    Unlike ``audit_*``, this returns a score even when the auditor is disabled
    — in that case the returned CanaryScore has overall=0 and ``error`` set,
    so callers can still store the raw response for future scoring.
    """
    if not is_enabled():
        return CanaryScore(
            overall=0.0,
            dimensions={},
            notes="",
            auditor_model="",
            error="auditor_disabled",
        )

    model = model_name()
    try:
        c = client if client is not None else _build_client()
        user = _CANARY_SCORE_USER_TEMPLATE.format(prompt=prompt, response=response)
        raw = _invoke(c, _CANARY_SCORE_SYSTEM, user)
        parsed = _extract_json(raw)
        dims = {k: int(v) for k, v in (parsed.get("dimensions") or {}).items()}
        overall = sum(dims.values()) / len(dims) if dims else 0.0
        return CanaryScore(
            overall=round(overall, 2),
            dimensions=dims,
            notes=str(parsed.get("notes", "")),
            auditor_model=model,
        )
    except Exception as e:  # noqa: BLE001
        return CanaryScore(
            overall=0.0,
            dimensions={},
            notes="",
            auditor_model=model,
            error=f"{type(e).__name__}: {e}",
        )
