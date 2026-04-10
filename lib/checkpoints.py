"""Metacognitive checkpoint scheduler."""

from __future__ import annotations

import random
from dataclasses import dataclass

from .modes import Mode
from .state import Session


@dataclass
class CheckpointResult:
    due: bool
    prompt: str = ""


def check_checkpoint(session: Session, mode: Mode) -> CheckpointResult:
    """Check if a metacognitive checkpoint is due based on message count.

    Returns a CheckpointResult with due=True and a randomly selected prompt
    if the interval has been reached.
    """
    interval = mode.metacognitive.checkpoint_interval
    if interval <= 0:
        return CheckpointResult(due=False)

    prompts = mode.metacognitive.prompts
    if not prompts:
        return CheckpointResult(due=False)

    messages_since_checkpoint = session.message_count - session.last_checkpoint_at
    if messages_since_checkpoint >= interval:
        prompt = random.choice(prompts)
        return CheckpointResult(due=True, prompt=prompt)

    return CheckpointResult(due=False)


def get_session_end_prompt(mode: Mode) -> str | None:
    """Get the session-end metacognitive prompt for the current mode, if any."""
    prompt = mode.metacognitive.session_end_prompt
    return prompt if prompt else None


def messages_until_checkpoint(session: Session, mode: Mode) -> int | None:
    """Return how many messages until the next checkpoint, or None if disabled."""
    interval = mode.metacognitive.checkpoint_interval
    if interval <= 0:
        return None

    messages_since = session.message_count - session.last_checkpoint_at
    remaining = interval - messages_since
    return max(0, remaining)
