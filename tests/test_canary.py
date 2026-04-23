"""Tests for canary storage, scoring, and trend computation."""
from __future__ import annotations

import json
import time

import pytest

from lib import canary
from lib.canary import CanaryAttempt, CanaryStore, compute_trend, submit_canary


class _FakeContent:
    def __init__(self, text: str):
        self.text = text


class _FakeMessage:
    def __init__(self, text: str):
        self.content = [_FakeContent(text)]


class _FakeMessages:
    def __init__(self, texts):
        self.texts = list(texts)
        self.calls = 0

    def create(self, **kwargs):
        text = self.texts[min(self.calls, len(self.texts) - 1)]
        self.calls += 1
        return _FakeMessage(text)


class _FakeClient:
    def __init__(self, texts):
        self.messages = _FakeMessages(texts)


def _enable(monkeypatch):
    monkeypatch.setenv("FORGE_AUDITOR_ENABLED", "1")


# ---------------------------------------------------------------------------
# Question bank
# ---------------------------------------------------------------------------

def test_every_question_has_stable_id():
    ids = [q["id"] for q in canary.CANARY_QUESTIONS]
    assert len(ids) == len(set(ids)), "duplicate canary prompt ids"
    assert all(isinstance(i, str) and i for i in ids)


def test_get_by_id_roundtrip():
    for q in canary.CANARY_QUESTIONS:
        got = canary.get_canary_question_by_id(q["id"])
        assert got is not None
        assert got["prompt"] == q["prompt"]


def test_get_by_id_unknown_returns_none():
    assert canary.get_canary_question_by_id("nope") is None


# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------

def test_store_records_and_reloads(tmp_path):
    store = CanaryStore(state_dir=tmp_path)
    attempt = CanaryAttempt(
        timestamp=1000.0,
        prompt_id="writing_email_decline",
        response="hello",
        overall=3.5,
        dimensions={"clarity": 4, "depth": 3, "independence": 4},
        notes="decent start",
        auditor_model="claude-sonnet-4-6",
    )
    store.record(attempt)

    # Reload from disk via a fresh store
    fresh = CanaryStore(state_dir=tmp_path)
    loaded = fresh.get_attempts("writing_email_decline")
    assert len(loaded) == 1
    assert loaded[0].overall == 3.5
    assert loaded[0].response == "hello"


def test_store_orders_attempts_chronologically(tmp_path):
    store = CanaryStore(state_dir=tmp_path)
    store.record(CanaryAttempt(timestamp=3000.0, prompt_id="x", response="c", overall=3.0))
    store.record(CanaryAttempt(timestamp=1000.0, prompt_id="x", response="a", overall=1.0))
    store.record(CanaryAttempt(timestamp=2000.0, prompt_id="x", response="b", overall=2.0))

    attempts = store.get_attempts("x")
    assert [a.response for a in attempts] == ["a", "b", "c"]


# ---------------------------------------------------------------------------
# Trend
# ---------------------------------------------------------------------------

def test_trend_empty_when_no_attempts(tmp_path):
    trend = compute_trend("writing_email_decline", store=CanaryStore(state_dir=tmp_path))
    assert trend.attempts == 0
    assert trend.last_score is None
    assert trend.slope_per_attempt is None


def test_trend_single_attempt(tmp_path):
    store = CanaryStore(state_dir=tmp_path)
    store.record(CanaryAttempt(timestamp=1.0, prompt_id="x", response="r", overall=3.0))

    trend = compute_trend("x", store=store)
    assert trend.attempts == 1
    assert trend.last_score == 3.0
    assert trend.prev_score is None
    assert trend.change_vs_prev is None
    assert trend.slope_per_attempt is None  # <2 points


def test_trend_improving(tmp_path):
    store = CanaryStore(state_dir=tmp_path)
    for i, overall in enumerate([2.0, 3.0, 3.5, 4.0, 4.5]):
        store.record(CanaryAttempt(timestamp=float(i), prompt_id="x", response="r", overall=overall))

    trend = compute_trend("x", store=store)
    assert trend.attempts == 5
    assert trend.last_score == 4.5
    assert trend.prev_score == 4.0
    assert trend.change_vs_prev == 0.5
    assert trend.slope_per_attempt is not None and trend.slope_per_attempt > 0


def test_trend_skips_errored_attempts(tmp_path):
    store = CanaryStore(state_dir=tmp_path)
    store.record(CanaryAttempt(timestamp=1.0, prompt_id="x", response="r", overall=0.0, error="auditor_disabled"))
    store.record(CanaryAttempt(timestamp=2.0, prompt_id="x", response="r", overall=3.5))

    trend = compute_trend("x", store=store)
    assert trend.attempts == 2  # total count includes the errored one
    assert trend.last_score == 3.5  # but only scored ones contribute to trend math
    assert trend.prev_score is None  # only 1 valid


# ---------------------------------------------------------------------------
# Full submit_canary flow
# ---------------------------------------------------------------------------

def test_submit_canary_stores_scored_attempt(tmp_path, monkeypatch):
    _enable(monkeypatch)
    payload = json.dumps({
        "dimensions": {"clarity": 4, "depth": 3, "independence": 5},
        "notes": "strong voice; opening is buried",
    })
    client = _FakeClient([payload])
    store = CanaryStore(state_dir=tmp_path)

    attempt, trend = submit_canary(
        "writing_email_decline",
        "Hi team, I cannot make it this week.",
        store=store,
        client=client,
    )

    assert attempt.overall == pytest.approx((4 + 3 + 5) / 3, abs=0.01)
    assert attempt.dimensions == {"clarity": 4, "depth": 3, "independence": 5}
    assert "buried" in attempt.notes
    assert attempt.error is None

    assert trend.attempts == 1
    assert trend.last_score == attempt.overall


def test_submit_canary_unknown_prompt_raises(tmp_path):
    store = CanaryStore(state_dir=tmp_path)
    with pytest.raises(ValueError, match="unknown canary prompt_id"):
        submit_canary("does_not_exist", "...", store=store)


def test_submit_canary_stores_even_when_auditor_disabled(tmp_path, monkeypatch):
    monkeypatch.delenv("FORGE_AUDITOR_ENABLED", raising=False)
    store = CanaryStore(state_dir=tmp_path)

    attempt, trend = submit_canary(
        "writing_email_decline",
        "Hi team,\nI cannot attend.",
        store=store,
        client=None,
    )

    # Auditor disabled → attempt stored with overall=0 and error=auditor_disabled
    assert attempt.overall == 0.0
    assert attempt.error == "auditor_disabled"
    # But it IS persisted so it can be rescored later
    fresh = CanaryStore(state_dir=tmp_path)
    assert len(fresh.get_attempts("writing_email_decline")) == 1


def test_submit_canary_trend_improves_over_attempts(tmp_path, monkeypatch):
    _enable(monkeypatch)
    payloads = [
        json.dumps({"dimensions": {"clarity": 2, "depth": 2, "independence": 2}, "notes": "thin"}),
        json.dumps({"dimensions": {"clarity": 3, "depth": 3, "independence": 3}, "notes": "better"}),
        json.dumps({"dimensions": {"clarity": 4, "depth": 4, "independence": 4}, "notes": "strong"}),
    ]
    client = _FakeClient(payloads)
    store = CanaryStore(state_dir=tmp_path)

    for i in range(3):
        time.sleep(0.01)  # ensure distinct timestamps
        submit_canary("writing_email_decline", f"attempt {i}", store=store, client=client)

    trend = compute_trend("writing_email_decline", store=store)
    assert trend.attempts == 3
    assert trend.last_score == 4.0
    assert trend.prev_score == 3.0
    assert trend.change_vs_prev == 1.0
    assert trend.slope_per_attempt is not None and trend.slope_per_attempt > 0
