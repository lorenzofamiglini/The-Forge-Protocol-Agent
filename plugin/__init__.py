"""Forge Protocol plugin for Hermes Agent.

Registers 6 tools and lifecycle hooks that enforce the Forge Protocol's
4 interaction modes (Forge, Anvil, Furnace, Executor) to protect human
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
_LIB_DIR = _REPO_ROOT / "lib"
_MODES_DIR = _REPO_ROOT / "modes"

if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

# Import our pure-Python core
from lib.checkpoints import check_checkpoint, get_session_end_prompt, messages_until_checkpoint
from lib.modes import load_all_modes, Mode
from lib.state import StateManager, Session
from lib.validator import validate_input, validate_output
from lib.audit import check_audit_reminders, compute_dependency_report

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
        "Validate user input against the current mode's requirements. "
        "Anvil requires a draft (100+ words), Furnace requires 3+ ideas, etc."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "user_input": {
                "type": "string",
                "description": "The user's message to validate.",
            },
            "mode": {
                "type": "string",
                "description": "Mode ID to validate against (forge/anvil/furnace/executor). Defaults to current session mode.",
            },
        },
        "required": ["user_input"],
    },
}

VALIDATE_OUTPUT_SCHEMA = {
    "name": "forge_validate_output",
    "description": (
        "Validate an LLM response against the current mode's output rules. "
        "Forge forbids direct answers and code generation; Anvil forbids rewrites; etc."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "response": {
                "type": "string",
                "description": "The LLM response to validate.",
            },
            "mode": {
                "type": "string",
                "description": "Mode ID to validate against. Defaults to current session mode.",
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
        "furnace (idea stress-tester), executor (normal AI, no friction)."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "mode": {
                "type": "string",
                "enum": ["forge", "anvil", "furnace", "executor"],
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

    result = validate_input(user_input, mode)
    return json.dumps({
        "passed": result.passed,
        "message": result.message,
        "mode": mode_id,
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

    result = validate_output(response, mode)
    return json.dumps({
        "passed": result.passed,
        "message": result.message,
        "violations": [
            {"rule_id": v.rule_id, "reason": v.reason}
            for v in result.violations
        ],
        "mode": mode_id,
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
        from lib.state import Violation
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


def _pre_tool_call(**kwargs: Any) -> dict | None:
    """Before each tool call, check if we should intervene.

    In Forge/Anvil/Furnace modes, warn if the agent is about to write
    code or files (which might bypass the thinking-first requirement).
    """
    if not _current_session_id:
        return None

    session = _get_session(_current_session_id)
    tool_name = kwargs.get("tool_name", "")

    # In thinking modes, flag direct code/file writes
    if session.current_mode in ("forge", "anvil", "furnace"):
        write_tools = {"write_file", "patch", "execute_code"}
        if tool_name in write_tools:
            return {
                "context": (
                    f"[Forge Protocol] Warning: You are in {session.current_mode} mode. "
                    f"Calling {tool_name} may bypass the thinking-first requirement. "
                    "Consider asking the user to write the code themselves."
                )
            }

    return None


# ---------------------------------------------------------------------------
# Plugin registration entry point
# ---------------------------------------------------------------------------

def register(ctx) -> None:
    """Called by Hermes PluginManager to register forge-protocol tools and hooks."""

    TOOLSET = "forge"

    # Register all 6 tools
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
        ("forge_log", LOG_SCHEMA, _handle_log,
         "Log interaction for audit trail"),
    ]

    emojis = {
        "forge_validate_input": "📥",
        "forge_validate_output": "📤",
        "forge_checkpoint": "🧠",
        "forge_get_state": "📊",
        "forge_set_mode": "🔄",
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
    ctx.register_hook("pre_tool_call", _pre_tool_call)

    logger.info("Forge Protocol plugin registered: 6 tools, 3 hooks")
