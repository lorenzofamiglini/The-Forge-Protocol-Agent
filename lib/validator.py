"""Return mode validation rules for LLM evaluation.

The LLM evaluates compliance — not regex. These functions return
the natural-language rules that the orchestrator LLM checks against.
"""

from __future__ import annotations

from dataclasses import dataclass

from .modes import Mode


@dataclass
class InputRules:
    """Rules the LLM should evaluate the user's input against."""
    mode: str
    mode_name: str
    rules: list[str]


@dataclass
class OutputRules:
    """Rules the LLM should evaluate its own response against."""
    mode: str
    mode_name: str
    required_behaviors: list[str]
    forbidden_behaviors: list[str]


def get_input_rules(mode: Mode) -> InputRules:
    """Return the mode's input requirements as natural language rules."""
    return InputRules(
        mode=mode.id,
        mode_name=mode.name,
        rules=mode.input_rules,
    )


def get_output_rules(mode: Mode) -> OutputRules:
    """Return the mode's output behavioral rules for LLM self-check."""
    return OutputRules(
        mode=mode.id,
        mode_name=mode.name,
        required_behaviors=mode.behaviors.required,
        forbidden_behaviors=mode.behaviors.forbidden,
    )
