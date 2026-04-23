"""Forge Protocol plugin for Hermes Agent.

Registers 9 tools and 2 lifecycle hooks that enforce the Forge Protocol's
4 interaction modes (Forge, Anvil, Crucible, Executor) to protect human
cognitive sovereignty when working with AI.
"""

from __future__ import annotations

import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Ensure lib/ is importable (forge-protocol repo root)
# ---------------------------------------------------------------------------

_PLUGIN_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _PLUGIN_DIR.parent

# Modes directory resolution (in priority order):
#   1. FORGE_MODES_DIR environment variable (explicit override)
#   2. <plugin-dir>/modes/   — copy-mode install (install.sh default)
#   3. <repo-root>/modes/    — dev/symlink mode, or pip-installed layout
_MODES_OVERRIDE = os.environ.get("FORGE_MODES_DIR")
if _MODES_OVERRIDE:
    _MODES_DIR = Path(_MODES_OVERRIDE).expanduser().resolve()
elif (_PLUGIN_DIR / "modes").is_dir():
    _MODES_DIR = _PLUGIN_DIR / "modes"
else:
    _MODES_DIR = _REPO_ROOT / "modes"

# lib/ import path — same two candidate locations as modes.
_LIB_DIR_CANDIDATES = [_PLUGIN_DIR / "lib", _REPO_ROOT / "lib"]
for _candidate in _LIB_DIR_CANDIDATES:
    if _candidate.is_dir():
        _parent = str(_candidate.parent)
        if _parent not in sys.path:
            sys.path.insert(0, _parent)
        break
else:
    # Fallback: add repo root (original behavior) even if lib/ isn't present yet.
    if str(_REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(_REPO_ROOT))

# Import our pure-Python core
from lib.checkpoints import check_checkpoint, get_session_end_prompt, messages_until_checkpoint
from lib.modes import load_all_modes, Mode
from lib.state import StateManager, Session, Violation
from lib.validator import get_input_rules, get_output_rules
from lib.audit import check_audit_reminders, compute_dependency_report
from lib import auditor as adversarial_auditor
from lib import canary as canary_module

# ---------------------------------------------------------------------------
# Shared state (initialized once per Hermes session)
# ---------------------------------------------------------------------------

_state_manager: StateManager | None = None
_modes: dict[str, Mode] = {}
_current_session_id: str | None = None


def _get_state_manager() -> StateManager:
    global _state_manager
    if _state_manager is None:
        _state_manager = StateManager()
    return _state_manager


def _get_modes() -> dict[str, Mode]:
    global _modes
    if not _modes:
        if _MODES_DIR.is_dir():
            _modes = load_all_modes(_MODES_DIR)
        else:
            logger.warning("Forge modes directory not found: %s", _MODES_DIR)
    return _modes


def _get_session(session_id: str | None = None) -> Session:
    sm = _get_state_manager()
    sid = session_id or _current_session_id or "default"
    return sm.get_or_create_session(sid)


def _get_mode(mode_id: str) -> Mode | None:
    modes = _get_modes()
    return modes.get(mode_id)


# ---------------------------------------------------------------------------
# Tool schemas (OpenAI function-calling format)
# ---------------------------------------------------------------------------

VALIDATE_INPUT_SCHEMA = {
    "name": "forge_validate_input",
    "description": (
        "Get the current mode's input requirements as natural language rules. "
        "You (the LLM) evaluate whether the user's input meets these rules."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "user_input": {
                "type": "string",
                "description": "The user's message — included for context in the response.",
            },
            "mode": {
                "type": "string",
                "description": "Mode ID (forge/anvil/crucible/executor). Defaults to current session mode.",
            },
        },
        "required": ["user_input"],
    },
}

VALIDATE_OUTPUT_SCHEMA = {
    "name": "forge_validate_output",
    "description": (
        "Get the current mode's behavioral rules (required and forbidden) for self-checking. "
        "You (the LLM) evaluate whether a response complies with these rules."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "response": {
                "type": "string",
                "description": "The LLM response to check — included for context.",
            },
            "mode": {
                "type": "string",
                "description": "Mode ID to check against. Defaults to current session mode.",
            },
        },
        "required": ["response"],
    },
}

CHECKPOINT_SCHEMA = {
    "name": "forge_checkpoint",
    "description": (
        "Check if a metacognitive checkpoint is due (periodic prompt that asks the user "
        "to reflect on whether the AI is doing their thinking for them)."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "session_id": {
                "type": "string",
                "description": "Session ID. Defaults to current session.",
            },
        },
        "required": [],
    },
}

GET_STATE_SCHEMA = {
    "name": "forge_get_state",
    "description": (
        "Get the current Forge Protocol state: active mode, message count, "
        "violations, audit status, and mode history."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "session_id": {
                "type": "string",
                "description": "Session ID. Defaults to current session.",
            },
        },
        "required": [],
    },
}

SET_MODE_SCHEMA = {
    "name": "forge_set_mode",
    "description": (
        "Switch the active Forge Protocol mode. Modes: "
        "forge (Socratic thinking partner), anvil (critic/editor), "
        "crucible (idea stress-tester), executor (normal AI, no friction)."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "mode": {
                "type": "string",
                "enum": ["forge", "anvil", "crucible", "executor"],
                "description": "The mode to switch to.",
            },
            "session_id": {
                "type": "string",
                "description": "Session ID. Defaults to current session.",
            },
        },
        "required": ["mode"],
    },
}

CANARY_LIST_SCHEMA = {
    "name": "forge_canary_list",
    "description": (
        "List the fixed set of canary prompts. The user answers these unassisted "
        "to measure whether their independent skills are improving or drifting "
        "over time. Each prompt has a stable id used when submitting a response."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "category": {
                "type": "string",
                "description": "Optional filter: writing, analysis, debugging, strategy, communication.",
            },
        },
        "required": [],
    },
}

CANARY_SUBMIT_SCHEMA = {
    "name": "forge_canary_submit",
    "description": (
        "Submit the user's unassisted answer to a canary prompt. The adversarial "
        "auditor scores the response on clarity, depth, and independence, stores "
        "it, and returns the skill trend (last score, change vs. previous, "
        "mean of last 5, linear slope across attempts). The attempt is stored "
        "even if the auditor is disabled, so it can be scored later."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "prompt_id": {
                "type": "string",
                "description": "The canary prompt id (e.g. 'writing_email_decline'). See forge_canary_list.",
            },
            "response": {
                "type": "string",
                "description": "The user's verbatim, unassisted response to the prompt.",
            },
        },
        "required": ["prompt_id", "response"],
    },
}

DEPENDENCY_REPORT_SCHEMA = {
    "name": "forge_dependency_report",
    "description": (
        "Compute the quarterly dependency audit: mode-usage ratios across all "
        "sessions, total violations, and an assessment of cognitive health. "
        "Updates the last_dependency_audit timestamp so the reminder clears."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "session_id": {
                "type": "string",
                "description": "Session ID used to record the audit completion. Defaults to current session.",
            },
        },
        "required": [],
    },
}

LOG_SCHEMA = {
    "name": "forge_log",
    "description": (
        "Log an interaction for the Forge Protocol audit trail. "
        "Increments message count and records any violations."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "session_id": {
                "type": "string",
                "description": "Session ID. Defaults to current session.",
            },
            "violation_type": {
                "type": "string",
                "description": "Type of violation if any ('input' or 'output').",
            },
            "rule_id": {
                "type": "string",
                "description": "ID of the violated rule.",
            },
            "message": {
                "type": "string",
                "description": "Description of the violation.",
            },
        },
        "required": [],
    },
}


# ---------------------------------------------------------------------------
# Tool handlers
# ---------------------------------------------------------------------------

def _handle_validate_input(args: dict, **kw) -> str:
    user_input = args.get("user_input", "")
    mode_id = args.get("mode")

    if not user_input:
        return json.dumps({"error": "user_input is required"})

    if not mode_id:
        session = _get_session()
        mode_id = session.current_mode

    mode = _get_mode(mode_id)
    if not mode:
        return json.dumps({"error": f"Unknown mode: {mode_id}"})

    rules = get_input_rules(mode)
    audit = adversarial_auditor.audit_input(user_input, rules)
    if audit is not None:
        return json.dumps({
            "mode": rules.mode,
            "mode_name": rules.mode_name,
            "input_rules": rules.rules,
            "audit": audit.to_dict(),
            "instruction": (
                "An independent auditor has evaluated the user's input against the rules. "
                "If audit.compliant is false, tell the user what's missing before engaging."
            ),
        })
    return json.dumps({
        "mode": rules.mode,
        "mode_name": rules.mode_name,
        "input_rules": rules.rules,
        "instruction": (
            "Evaluate the user's input against these rules. "
            "If the input doesn't meet a rule, tell the user what's needed."
        ),
    })


def _handle_validate_output(args: dict, **kw) -> str:
    response = args.get("response", "")
    mode_id = args.get("mode")

    if not response:
        return json.dumps({"error": "response is required"})

    if not mode_id:
        session = _get_session()
        mode_id = session.current_mode

    mode = _get_mode(mode_id)
    if not mode:
        return json.dumps({"error": f"Unknown mode: {mode_id}"})

    rules = get_output_rules(mode)
    audit = adversarial_auditor.audit_output(response, rules)
    if audit is not None:
        return json.dumps({
            "mode": rules.mode,
            "mode_name": rules.mode_name,
            "required_behaviors": rules.required_behaviors,
            "forbidden_behaviors": rules.forbidden_behaviors,
            "audit": audit.to_dict(),
            "instruction": (
                "An independent auditor has evaluated this response against the rules. "
                "If audit.compliant is false, regenerate or amend to address the listed violations."
            ),
        })
    return json.dumps({
        "mode": rules.mode,
        "mode_name": rules.mode_name,
        "required_behaviors": rules.required_behaviors,
        "forbidden_behaviors": rules.forbidden_behaviors,
        "instruction": (
            "Check this response against the mode rules. "
            "If it violates any forbidden behavior or misses a required behavior, flag it."
        ),
    })


def _handle_checkpoint(args: dict, **kw) -> str:
    session_id = args.get("session_id")
    session = _get_session(session_id)
    mode = _get_mode(session.current_mode)

    if not mode:
        return json.dumps({"due": False, "reason": "Unknown mode"})

    result = check_checkpoint(session, mode)
    remaining = messages_until_checkpoint(session, mode)

    response = {
        "due": result.due,
        "prompt": result.prompt if result.due else "",
        "messages_until_next": remaining,
        "current_mode": session.current_mode,
    }

    if result.due:
        # Update in-memory and write once (avoid redundant disk read)
        session.last_checkpoint_at = session.message_count
        session.updated_at = time.time()
        sm = _get_state_manager()
        sm._write_session(session)

    return json.dumps(response)


def _handle_get_state(args: dict, **kw) -> str:
    session_id = args.get("session_id")
    session = _get_session(session_id)

    # Check audit reminders
    reminders = check_audit_reminders(session)

    return json.dumps({
        "session_id": session.session_id,
        "current_mode": session.current_mode,
        "message_count": session.message_count,
        "last_checkpoint_at": session.last_checkpoint_at,
        "violation_count": len(session.violations),
        "recent_violations": [
            {"rule_id": v.rule_id, "mode": v.mode, "type": v.violation_type}
            for v in session.violations[-5:]
        ],
        "mode_history": [
            {"mode": e.mode, "messages": e.message_count}
            for e in session.mode_history
        ],
        "audit_reminders": [
            {"type": r.audit_type, "message": r.message, "overdue_days": r.overdue_days}
            for r in reminders
        ],
    })


def _handle_set_mode(args: dict, **kw) -> str:
    new_mode = args.get("mode", "")
    session_id = args.get("session_id")

    modes = _get_modes()
    if new_mode not in modes:
        valid = ", ".join(sorted(modes.keys()))
        return json.dumps({"error": f"Invalid mode: {new_mode}. Valid: {valid}"})

    session = _get_session(session_id)
    previous = session.current_mode

    if previous == new_mode:
        return json.dumps({
            "previous": previous,
            "current": new_mode,
            "changed": False,
            "message": f"Already in {new_mode} mode.",
        })

    sm = _get_state_manager()
    session = sm.switch_mode(session.session_id, new_mode)

    # Load mode info for the response
    mode = _get_mode(new_mode)
    mode_desc = mode.description if mode else ""

    return json.dumps({
        "previous": previous,
        "current": new_mode,
        "changed": True,
        "description": mode_desc,
        "message": f"Switched from {previous} to {new_mode} mode.",
    })


def _handle_canary_list(args: dict, **kw) -> str:
    category = args.get("category")
    questions = canary_module.list_canary_questions()
    if category:
        questions = [q for q in questions if q.get("category") == category]
    return json.dumps({"questions": questions})


def _handle_canary_submit(args: dict, **kw) -> str:
    prompt_id = args.get("prompt_id", "")
    response = args.get("response", "")

    if not prompt_id:
        return json.dumps({"error": "prompt_id is required"})
    if not response or not response.strip():
        return json.dumps({"error": "response is required (non-empty)"})

    try:
        attempt, trend = canary_module.submit_canary(prompt_id, response)
    except ValueError as e:
        return json.dumps({"error": str(e)})

    # Update audit timestamp (records that a canary was run)
    if _current_session_id:
        sm = _get_state_manager()
        try:
            sm.update_audit(_current_session_id, "canary")
        except ValueError:
            pass  # session not found — non-fatal

    return json.dumps({
        "prompt_id": prompt_id,
        "attempt": {
            "timestamp": attempt.timestamp,
            "overall": attempt.overall,
            "dimensions": attempt.dimensions,
            "notes": attempt.notes,
            "auditor_model": attempt.auditor_model,
            "error": attempt.error,
        },
        "trend": {
            "attempts": trend.attempts,
            "last_score": trend.last_score,
            "prev_score": trend.prev_score,
            "change_vs_prev": trend.change_vs_prev,
            "mean_last_5": trend.mean_last_5,
            "slope_per_attempt": trend.slope_per_attempt,
        },
    })


def _handle_dependency_report(args: dict, **kw) -> str:
    session_id = args.get("session_id") or _current_session_id
    sm = _get_state_manager()
    report = compute_dependency_report(sm)

    # Mark the quarterly audit as completed so its reminder clears.
    if session_id:
        try:
            sm.update_audit(session_id, "dependency")
        except ValueError:
            pass  # session not found — non-fatal

    return json.dumps({
        "total_sessions": report.total_sessions,
        "total_messages": report.total_messages,
        "mode_ratios": {
            "forge": report.mode_ratios.forge,
            "anvil": report.mode_ratios.anvil,
            "crucible": report.mode_ratios.crucible,
            "executor": report.mode_ratios.executor,
        },
        "total_violations": report.total_violations,
        "assessment": report.assessment,
    })


def _handle_log(args: dict, **kw) -> str:
    session_id = args.get("session_id")
    violation_type = args.get("violation_type")
    rule_id = args.get("rule_id")
    message = args.get("message", "")

    sm = _get_state_manager()
    session = _get_session(session_id)

    # Mutate in-memory and write once (avoid multiple disk round-trips)
    session.message_count += 1
    session.updated_at = time.time()

    violation_logged = False
    if violation_type and rule_id:
        session.violations.append(
            Violation(
                timestamp=time.time(),
                mode=session.current_mode,
                violation_type=violation_type,
                rule_id=rule_id,
                message=message,
            )
        )
        violation_logged = True

    sm._write_session(session)

    return json.dumps({
        "logged": True,
        "message_count": session.message_count,
        "violation_logged": violation_logged,
    })


# ---------------------------------------------------------------------------
# Lifecycle hooks
# ---------------------------------------------------------------------------

def _on_session_start(**kwargs: Any) -> None:
    """Initialize forge state when a Hermes session starts."""
    global _current_session_id

    session_id = kwargs.get("session_id", f"hermes-{int(time.time())}")
    _current_session_id = session_id

    sm = _get_state_manager()
    session = sm.get_or_create_session(session_id)
    logger.info(
        "Forge Protocol active — mode: %s, messages: %d",
        session.current_mode,
        session.message_count,
    )


def _on_session_end(**kwargs: Any) -> None:
    """Inject session-end reflection prompt if appropriate."""
    if not _current_session_id:
        return

    session = _get_session(_current_session_id)
    mode = _get_mode(session.current_mode)
    if not mode:
        return

    end_prompt = get_session_end_prompt(mode)
    if end_prompt:
        logger.info("Forge session-end prompt: %s", end_prompt[:80])


# ---------------------------------------------------------------------------
# Plugin registration entry point
# ---------------------------------------------------------------------------

def register(ctx) -> None:
    """Called by Hermes PluginManager to register forge-protocol tools and hooks."""

    TOOLSET = "forge"

    # Register all tools
    tools = [
        ("forge_validate_input", VALIDATE_INPUT_SCHEMA, _handle_validate_input,
         "Validate input against mode requirements"),
        ("forge_validate_output", VALIDATE_OUTPUT_SCHEMA, _handle_validate_output,
         "Validate LLM output against mode rules"),
        ("forge_checkpoint", CHECKPOINT_SCHEMA, _handle_checkpoint,
         "Check if metacognitive checkpoint is due"),
        ("forge_get_state", GET_STATE_SCHEMA, _handle_get_state,
         "Get current Forge Protocol state"),
        ("forge_set_mode", SET_MODE_SCHEMA, _handle_set_mode,
         "Switch Forge Protocol mode"),
        ("forge_canary_list", CANARY_LIST_SCHEMA, _handle_canary_list,
         "List canary prompts for skill tracking"),
        ("forge_canary_submit", CANARY_SUBMIT_SCHEMA, _handle_canary_submit,
         "Submit and score an unassisted canary response"),
        ("forge_dependency_report", DEPENDENCY_REPORT_SCHEMA, _handle_dependency_report,
         "Compute quarterly mode-usage dependency audit"),
        ("forge_log", LOG_SCHEMA, _handle_log,
         "Log interaction for audit trail"),
    ]

    emojis = {
        "forge_validate_input": "📥",
        "forge_validate_output": "📤",
        "forge_checkpoint": "🧠",
        "forge_get_state": "📊",
        "forge_set_mode": "🔄",
        "forge_canary_list": "🐤",
        "forge_canary_submit": "📈",
        "forge_dependency_report": "📉",
        "forge_log": "📝",
    }

    for name, schema, handler, description in tools:
        ctx.register_tool(
            name=name,
            toolset=TOOLSET,
            schema=schema,
            handler=handler,
            description=description,
            emoji=emojis.get(name, "🔥"),
        )

    # Register lifecycle hooks
    ctx.register_hook("on_session_start", _on_session_start)
    ctx.register_hook("on_session_end", _on_session_end)

    logger.info("Forge Protocol plugin registered: 9 tools, 2 hooks")
