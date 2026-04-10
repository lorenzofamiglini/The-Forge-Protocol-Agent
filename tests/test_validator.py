"""Tests for input and output validation."""

from pathlib import Path

import pytest

from lib.modes import load_mode
from lib.validator import validate_input, validate_output

MODES_DIR = Path(__file__).parent.parent / "modes"


@pytest.fixture
def forge_mode():
    return load_mode(MODES_DIR / "forge.yaml")


@pytest.fixture
def anvil_mode():
    return load_mode(MODES_DIR / "anvil.yaml")


@pytest.fixture
def furnace_mode():
    return load_mode(MODES_DIR / "furnace.yaml")


@pytest.fixture
def executor_mode():
    return load_mode(MODES_DIR / "executor.yaml")


# --- Input validation ---


class TestInputValidation:
    def test_forge_accepts_any_input(self, forge_mode):
        result = validate_input("What do you think?", forge_mode)
        assert result.passed is True

    def test_anvil_rejects_short_input(self, anvil_mode):
        result = validate_input("fix this", anvil_mode)
        assert result.passed is False
        assert "draft" in result.message.lower() or "sentence" in result.message.lower()

    def test_anvil_accepts_draft(self, anvil_mode):
        draft = (
            "Here is my draft email to the team. "
            "I want to communicate the deadline change effectively. "
            "The project timeline has shifted by two weeks due to dependency delays. "
            "We need to realign our milestones accordingly. "
        ) * 5  # make it long enough
        result = validate_input(draft, anvil_mode)
        assert result.passed is True

    def test_furnace_rejects_single_idea(self, furnace_mode):
        result = validate_input("I think we should use microservices.", furnace_mode)
        assert result.passed is False
        assert "3" in result.message

    def test_furnace_accepts_three_ideas(self, furnace_mode):
        ideas = """1. Use microservices architecture
2. Implement event-driven communication
3. Deploy with Kubernetes for orchestration"""
        result = validate_input(ideas, furnace_mode)
        assert result.passed is True

    def test_executor_accepts_anything(self, executor_mode):
        result = validate_input("format this json", executor_mode)
        assert result.passed is True


# --- Output validation ---


class TestOutputValidation:
    def test_forge_rejects_direct_answer(self, forge_mode):
        response = "Here's how to solve this problem: first, you need to..."
        result = validate_output(response, forge_mode)
        assert result.passed is False
        assert any(v.rule_id == "direct-answer" for v in result.violations)

    def test_forge_rejects_code_generation(self, forge_mode):
        response = "```python\ndef solve():\n    return 42\n```"
        result = validate_output(response, forge_mode)
        assert result.passed is False
        assert any(v.rule_id == "code-generation" for v in result.violations)

    def test_forge_requires_question(self, forge_mode):
        response = "That's an interesting approach. I think it could work well."
        result = validate_output(response, forge_mode)
        assert result.passed is False
        assert any(v.rule_id == "contains-question" for v in result.violations)

    def test_forge_accepts_socratic_response(self, forge_mode):
        response = (
            "Interesting position. Let me push back on a few things:\n"
            "What specifically do you mean by 'scalable' in this context?\n"
            "What evidence do you have that this approach works at your scale?"
        )
        result = validate_output(response, forge_mode)
        assert result.passed is True

    def test_anvil_rejects_rewrite(self, anvil_mode):
        response = "Here's a revised version of your email:\n\nDear team..."
        result = validate_output(response, anvil_mode)
        assert result.passed is False

    def test_anvil_accepts_critique(self, anvil_mode):
        response = (
            "**Clarity**: 3/5 — The opening paragraph buries the main point.\n"
            "**Precision**: 4/5 — Claims are mostly specific.\n"
            "**Structure**: 2/5 — The argument flows backward.\n"
            "**Tone**: 4/5 — Appropriate for the audience.\n"
            "**Persuasiveness**: 3/5 — The ask is unclear.\n"
            "**Concision**: 3/5 — Paragraph 3 can be cut entirely.\n\n"
            "Where do you disagree with my assessment?"
        )
        result = validate_output(response, anvil_mode)
        assert result.passed is True

    def test_furnace_rejects_idea_generation(self, furnace_mode):
        response = "Here are some ideas you could also consider:\n1. Use GraphQL\n2. Try serverless"
        result = validate_output(response, furnace_mode)
        assert result.passed is False

    def test_executor_accepts_anything(self, executor_mode):
        response = "Here's the formatted JSON:\n```json\n{\"key\": \"value\"}\n```"
        result = validate_output(response, executor_mode)
        assert result.passed is True
