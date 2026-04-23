"""Tests for validation rule retrieval."""

from pathlib import Path

import pytest

from lib.modes import load_mode
from lib.validator import get_input_rules, get_output_rules

MODES_DIR = Path(__file__).parent.parent / "modes"


@pytest.fixture
def forge_mode():
    return load_mode(MODES_DIR / "forge.yaml")


@pytest.fixture
def anvil_mode():
    return load_mode(MODES_DIR / "anvil.yaml")


@pytest.fixture
def crucible_mode():
    return load_mode(MODES_DIR / "crucible.yaml")


@pytest.fixture
def executor_mode():
    return load_mode(MODES_DIR / "executor.yaml")


class TestInputRules:
    def test_forge_returns_rules(self, forge_mode):
        rules = get_input_rules(forge_mode)
        assert rules.mode == "forge"
        assert rules.mode_name == "Forge Mode"
        assert len(rules.rules) > 0

    def test_anvil_requires_draft(self, anvil_mode):
        rules = get_input_rules(anvil_mode)
        assert rules.mode == "anvil"
        assert any("draft" in r.lower() for r in rules.rules)

    def test_crucible_requires_ideas(self, crucible_mode):
        rules = get_input_rules(crucible_mode)
        assert rules.mode == "crucible"
        assert any("3" in r or "ideas" in r.lower() for r in rules.rules)

    def test_executor_has_no_input_rules(self, executor_mode):
        rules = get_input_rules(executor_mode)
        assert rules.mode == "executor"
        assert len(rules.rules) == 0


class TestOutputRules:
    def test_forge_has_forbidden_behaviors(self, forge_mode):
        rules = get_output_rules(forge_mode)
        assert rules.mode == "forge"
        assert len(rules.forbidden_behaviors) > 0
        assert any("direct answer" in b.lower() for b in rules.forbidden_behaviors)

    def test_forge_has_required_behaviors(self, forge_mode):
        rules = get_output_rules(forge_mode)
        assert len(rules.required_behaviors) > 0
        assert any("question" in b.lower() for b in rules.required_behaviors)

    def test_anvil_forbids_rewrites(self, anvil_mode):
        rules = get_output_rules(anvil_mode)
        assert any("rewrite" in b.lower() or "revised" in b.lower() for b in rules.forbidden_behaviors)

    def test_crucible_forbids_idea_generation(self, crucible_mode):
        rules = get_output_rules(crucible_mode)
        assert any("generate" in b.lower() for b in rules.forbidden_behaviors)

    def test_executor_has_no_forbidden_behaviors(self, executor_mode):
        rules = get_output_rules(executor_mode)
        assert len(rules.forbidden_behaviors) == 0
        assert len(rules.required_behaviors) > 0
