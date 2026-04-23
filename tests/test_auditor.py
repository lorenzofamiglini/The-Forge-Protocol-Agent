"""Tests for the adversarial auditor.

The auditor is opt-in (env-gated) and uses the anthropic SDK at runtime.
Tests here verify behavior with a fake client so no network calls are made.
"""
from __future__ import annotations

import json

import pytest

from lib import auditor as aud
from lib.validator import InputRules, OutputRules


class _FakeContent:
    def __init__(self, text: str):
        self.text = text


class _FakeMessage:
    def __init__(self, text: str):
        self.content = [_FakeContent(text)]


class _FakeMessages:
    def __init__(self, text: str):
        self.text = text
        self.calls: list[dict] = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return _FakeMessage(self.text)


class _FakeClient:
    def __init__(self, text: str):
        self.messages = _FakeMessages(text)


def _enable_auditor(monkeypatch):
    monkeypatch.setenv("FORGE_AUDITOR_ENABLED", "1")
    monkeypatch.setenv("FORGE_AUDITOR_MODEL", "claude-sonnet-4-6")


def test_disabled_by_default(monkeypatch):
    monkeypatch.delenv("FORGE_AUDITOR_ENABLED", raising=False)
    rules = OutputRules(mode="forge", mode_name="Forge Mode",
                        required_behaviors=["ask questions"], forbidden_behaviors=["give answers"])
    assert aud.audit_output("hello", rules) is None
    assert aud.audit_input("hi", InputRules(mode="forge", mode_name="Forge Mode", rules=["articulate"])) is None


def test_enabled_flag_accepts_multiple_values(monkeypatch):
    for value in ("1", "true", "TRUE", "yes", "on"):
        monkeypatch.setenv("FORGE_AUDITOR_ENABLED", value)
        assert aud.is_enabled() is True
    for value in ("0", "false", "", "no"):
        monkeypatch.setenv("FORGE_AUDITOR_ENABLED", value)
        assert aud.is_enabled() is False


def test_audit_output_compliant(monkeypatch):
    _enable_auditor(monkeypatch)
    client = _FakeClient(json.dumps({"compliant": True, "violations": []}))
    rules = OutputRules(
        mode="forge", mode_name="Forge Mode",
        required_behaviors=["ask at least one question"],
        forbidden_behaviors=["provide direct answers"],
    )
    result = aud.audit_output("What's your position on this?", rules, client=client)
    assert result is not None
    assert result.compliant is True
    assert result.violations == []
    assert result.auditor_model == "claude-sonnet-4-6"
    # Verify the auditor passed rules into the prompt
    call = client.messages.calls[0]
    assert "ask at least one question" in call["messages"][0]["content"]
    assert "provide direct answers" in call["messages"][0]["content"]


def test_audit_output_flags_violations(monkeypatch):
    _enable_auditor(monkeypatch)
    payload = {
        "compliant": False,
        "violations": [
            {
                "rule": "provide direct answers",
                "kind": "forbidden",
                "quote": "You should use microservices.",
                "reason": "That is a direct answer to a thinking question.",
            }
        ],
    }
    client = _FakeClient(json.dumps(payload))
    rules = OutputRules(
        mode="forge", mode_name="Forge Mode",
        required_behaviors=[], forbidden_behaviors=["provide direct answers"],
    )
    result = aud.audit_output("You should use microservices.", rules, client=client)
    assert result is not None
    assert result.compliant is False
    assert len(result.violations) == 1
    v = result.violations[0]
    assert v.kind == "forbidden"
    assert "microservices" in v.quote


def test_audit_output_extracts_json_from_prose(monkeypatch):
    _enable_auditor(monkeypatch)
    wrapped = 'Here is my judgment:\n```json\n{"compliant": true, "violations": []}\n```\nEnd.'
    client = _FakeClient(wrapped)
    rules = OutputRules(mode="anvil", mode_name="Anvil", required_behaviors=[], forbidden_behaviors=[])
    result = aud.audit_output("a response", rules, client=client)
    assert result is not None
    assert result.compliant is True
    assert result.error is None


def test_audit_output_handles_malformed_json(monkeypatch):
    _enable_auditor(monkeypatch)
    client = _FakeClient("not json at all")
    rules = OutputRules(mode="anvil", mode_name="Anvil", required_behaviors=[], forbidden_behaviors=[])
    result = aud.audit_output("a response", rules, client=client)
    assert result is not None
    # Errors are non-blocking — compliant defaults to True so the tool call doesn't break
    assert result.compliant is True
    assert result.error is not None
    assert "no JSON object" in result.error or "JSON" in result.error


def test_audit_input_skips_when_no_rules(monkeypatch):
    _enable_auditor(monkeypatch)
    rules = InputRules(mode="executor", mode_name="Executor", rules=[])
    # Should short-circuit without calling the client
    result = aud.audit_input("anything", rules, client=_FakeClient("ignored"))
    assert result is not None
    assert result.compliant is True
    assert result.violations == []


def test_audit_input_flags_fragment_dumping(monkeypatch):
    _enable_auditor(monkeypatch)
    payload = {
        "compliant": False,
        "violations": [
            {
                "rule": "User must articulate their own position",
                "kind": "input",
                "quote": "",
                "reason": "User submitted only a vague topic, not a position.",
            }
        ],
    }
    client = _FakeClient(json.dumps(payload))
    rules = InputRules(mode="forge", mode_name="Forge Mode",
                       rules=["User must articulate their own position"])
    result = aud.audit_input("microservices?", rules, client=client)
    assert result is not None
    assert result.compliant is False
    assert result.violations[0].kind == "input"


def test_score_canary_disabled_returns_error(monkeypatch):
    monkeypatch.delenv("FORGE_AUDITOR_ENABLED", raising=False)
    score = aud.score_canary("prompt", "response")
    assert score.overall == 0.0
    assert score.error == "auditor_disabled"


def test_score_canary_returns_scored_dimensions(monkeypatch):
    _enable_auditor(monkeypatch)
    payload = {
        "dimensions": {"clarity": 4, "depth": 3, "independence": 5},
        "notes": "Clear voice; the second paragraph is templated.",
    }
    client = _FakeClient(json.dumps(payload))
    score = aud.score_canary("Write an email.", "Hi team,\n\nProposal attached.", client=client)
    assert score.overall == pytest.approx((4 + 3 + 5) / 3, abs=0.01)
    assert score.dimensions == {"clarity": 4, "depth": 3, "independence": 5}
    assert "templated" in score.notes


def test_score_canary_handles_errors(monkeypatch):
    _enable_auditor(monkeypatch)
    client = _FakeClient("garbage")
    score = aud.score_canary("prompt", "response", client=client)
    assert score.overall == 0.0
    assert score.error is not None
