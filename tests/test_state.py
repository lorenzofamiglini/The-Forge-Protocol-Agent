"""Tests for state management."""

import json
import os
import tempfile
from pathlib import Path

import pytest

from lib.state import Session, StateManager


@pytest.fixture
def state_dir(tmp_path):
    return tmp_path / "forge-state"


@pytest.fixture
def sm(state_dir):
    return StateManager(state_dir)


def test_create_session(sm):
    session = sm.create_session("test-1")
    assert session.session_id == "test-1"
    assert session.current_mode == "executor"
    assert session.message_count == 0
    assert len(session.mode_history) == 1
    assert session.mode_history[0].mode == "executor"


def test_create_session_with_initial_mode(sm):
    session = sm.create_session("test-2", initial_mode="forge")
    assert session.current_mode == "forge"
    assert session.mode_history[0].mode == "forge"


def test_get_session(sm):
    sm.create_session("test-3")
    session = sm.get_session("test-3")
    assert session is not None
    assert session.session_id == "test-3"


def test_get_nonexistent_session(sm):
    assert sm.get_session("nonexistent") is None


def test_get_or_create_session(sm):
    session = sm.get_or_create_session("test-4")
    assert session.session_id == "test-4"
    # Second call returns the same session
    session2 = sm.get_or_create_session("test-4")
    assert session2.session_id == "test-4"


def test_switch_mode(sm):
    sm.create_session("test-5")
    session = sm.switch_mode("test-5", "forge")
    assert session.current_mode == "forge"
    assert len(session.mode_history) == 2
    assert session.mode_history[0].mode == "executor"
    assert session.mode_history[0].exited_at is not None
    assert session.mode_history[1].mode == "forge"


def test_switch_to_same_mode_is_noop(sm):
    sm.create_session("test-6", initial_mode="forge")
    session = sm.switch_mode("test-6", "forge")
    assert len(session.mode_history) == 1


def test_increment_messages(sm):
    sm.create_session("test-7")
    count = sm.increment_messages("test-7")
    assert count == 1
    count = sm.increment_messages("test-7")
    assert count == 2


def test_log_violation(sm):
    sm.create_session("test-8")
    sm.log_violation("test-8", "forge", "output", "direct-answer", "Gave a direct answer")
    session = sm.get_session("test-8")
    assert len(session.violations) == 1
    assert session.violations[0].rule_id == "direct-answer"


def test_update_checkpoint(sm):
    sm.create_session("test-9")
    sm.increment_messages("test-9")
    sm.increment_messages("test-9")
    sm.update_checkpoint("test-9")
    session = sm.get_session("test-9")
    assert session.last_checkpoint_at == 2


def test_update_audit(sm):
    sm.create_session("test-10")
    sm.update_audit("test-10", "canary")
    session = sm.get_session("test-10")
    assert session.audit_status.last_canary is not None
    assert session.audit_status.last_stress_test is None


def test_list_sessions(sm):
    sm.create_session("a")
    sm.create_session("b")
    sm.create_session("c")
    sessions = sm.list_sessions()
    assert set(sessions) == {"a", "b", "c"}


def test_session_persists_to_disk(sm, state_dir):
    sm.create_session("persist-test")
    path = state_dir / "sessions" / "persist-test.json"
    assert path.exists()
    with open(path) as f:
        data = json.load(f)
    assert data["session_id"] == "persist-test"


def test_switch_mode_on_nonexistent_session(sm):
    with pytest.raises(ValueError, match="Session not found"):
        sm.switch_mode("nonexistent", "forge")
