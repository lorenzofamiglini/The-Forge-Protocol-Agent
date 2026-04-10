"""Input and output validation against mode rules."""

from __future__ import annotations

from dataclasses import dataclass, field

from .modes import Mode
from .patterns import (
    PatternMatch,
    check_deny_patterns,
    check_require_patterns,
    count_ideas,
    count_sentences,
    detect_draft,
)


@dataclass
class ValidationResult:
    passed: bool
    message: str = ""
    violations: list[PatternMatch] = field(default_factory=list)


def validate_input(user_input: str, mode: Mode) -> ValidationResult:
    """Validate user input against mode's input requirements.

    Returns ValidationResult with passed=False and a user-facing message
    if the input doesn't meet requirements.
    """
    req = mode.input_requirements

    # Check minimum sentences
    if req.min_sentences > 0:
        sentence_count = count_sentences(user_input)
        if sentence_count < req.min_sentences:
            return ValidationResult(
                passed=False,
                message=(
                    f"{mode.name} requires at least {req.min_sentences} sentence(s) "
                    f"from you before the LLM responds. You wrote {sentence_count}. "
                    f"Write your thoughts out more fully first."
                ),
            )

    # Check draft requirement
    if req.require_draft:
        if not detect_draft(user_input):
            return ValidationResult(
                passed=False,
                message=(
                    f"{mode.name} requires you to submit your own draft first. "
                    f"Write at least 100 words of prose or a code block, "
                    f"then submit for critique."
                ),
            )

    # Check ideas count
    if req.require_ideas_count > 0:
        idea_count = count_ideas(user_input)
        if idea_count < req.require_ideas_count:
            return ValidationResult(
                passed=False,
                message=(
                    f"{mode.name} requires at least {req.require_ideas_count} ideas "
                    f"from you before engaging. You provided {idea_count}. "
                    f"List your ideas as numbered or bulleted items."
                ),
            )

    return ValidationResult(passed=True)


def validate_output(response: str, mode: Mode) -> ValidationResult:
    """Validate LLM output against mode's output rules.

    Returns ValidationResult with violations if the output breaks mode constraints.
    """
    violations: list[PatternMatch] = []

    violations.extend(check_deny_patterns(response, mode.output_validation.deny_patterns))
    violations.extend(check_require_patterns(response, mode.output_validation.require_patterns))

    if violations:
        reasons = [v.reason for v in violations]
        return ValidationResult(
            passed=False,
            message=f"Output violated {mode.name} rules: {'; '.join(reasons)}",
            violations=violations,
        )

    return ValidationResult(passed=True)
