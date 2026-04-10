"""Tests for metacognitive checkpoint scheduling."""

from pathlib import Path

import pytest

from lib.checkpoints import check_checkpoint, get_session_end_prompt, messages_until_checkpoint
from lib.modes import load_mode
from lib.state import Session, ModeEntry

MODES_DIR = Path(__file__).parent.parent / "modes"


@pytest.fixture
def forge_mode():
    return load_mode(MODES_DIR / "forge.yaml")


@pytest.fixture
def executor_mode():
    return load_mode(MODES_DIR / "executor.yaml")


def _make_session(message_count: int = 0, last_checkpoint_at: int = 0) -> Session:
    return Session(
        session_id="test",
        current_mode="forge",
        message_count=message_count,
        last_checkpoint_at=last_checkpoint_at,
    )


class TestCheckpoints:
    def test_checkpoint_not_due_at_zero(self, forge_mode):
        session = _make_session(message_count=0)
        result = check_checkpoint(session, forge_mode)
        assert result.due is False

    def test_checkpoint_not_due_before_interval(self, forge_mode):
        session = _make_session(message_count=3)
        result = check_checkpoint(session, forge_mode)
        assert result.due is False

    def test_checkpoint_due_at_interval(self, forge_mode):
        session = _make_session(message_count=5)
        result = check_checkpoint(session, forge_mode)
        assert result.due is True
        assert result.prompt  # should have a prompt

    def test_checkpoint_due_after_reset(self, forge_mode):
        session = _make_session(message_count=10, last_checkpoint_at=5)
        result = check_checkpoint(session, forge_mode)
        assert result.due is True

    def test_checkpoint_not_due_right_after_checkpoint(self, forge_mode):
        session = _make_session(message_count=7, last_checkpoint_at=5)
        result = check_checkpoint(session, forge_mode)
        assert result.due is False

    def test_executor_never_has_checkpoints(self, executor_mode):
        session = _make_session(message_count=100)
        result = check_checkpoint(session, executor_mode)
        assert result.due is False

    def test_session_end_prompt_for_forge(self, forge_mode):
        prompt = get_session_end_prompt(forge_mode)
        assert prompt is not None
        assert len(prompt) > 0

    def test_no_session_end_prompt_for_executor(self, executor_mode):
        prompt = get_session_end_prompt(executor_mode)
        assert prompt is None

    def test_messages_until_checkpoint(self, forge_mode):
        session = _make_session(message_count=2)
        remaining = messages_until_checkpoint(session, forge_mode)
        assert remaining == 3

    def test_messages_until_checkpoint_none_for_executor(self, executor_mode):
        session = _make_session(message_count=2)
        remaining = messages_until_checkpoint(session, executor_mode)
        assert remaining is None
