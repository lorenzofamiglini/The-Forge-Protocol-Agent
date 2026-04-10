"""Tests for mode loading and validation."""

import os
from pathlib import Path

import pytest

from lib.modes import Mode, load_all_modes, load_mode, validate_mode_id

MODES_DIR = Path(__file__).parent.parent / "modes"


def test_load_all_modes():
    modes = load_all_modes(MODES_DIR)
    assert len(modes) == 4
    assert set(modes.keys()) == {"forge", "anvil", "furnace", "executor"}


def test_each_mode_has_required_fields():
    modes = load_all_modes(MODES_DIR)
    for mode_id, mode in modes.items():
        assert mode.id == mode_id
        assert mode.name
        assert mode.description
        assert mode.system_prompt_file


def test_forge_mode_has_behaviors():
    mode = load_mode(MODES_DIR / "forge.yaml")
    assert len(mode.behaviors.required) > 0
    assert len(mode.behaviors.forbidden) > 0


def test_forge_mode_has_deny_patterns():
    mode = load_mode(MODES_DIR / "forge.yaml")
    assert len(mode.output_validation.deny_patterns) > 0
    ids = [p.id for p in mode.output_validation.deny_patterns]
    assert "direct-answer" in ids


def test_forge_mode_requires_question_in_output():
    mode = load_mode(MODES_DIR / "forge.yaml")
    assert len(mode.output_validation.require_patterns) > 0
    ids = [p.id for p in mode.output_validation.require_patterns]
    assert "contains-question" in ids


def test_anvil_mode_requires_draft():
    mode = load_mode(MODES_DIR / "anvil.yaml")
    assert mode.input_requirements.require_draft is True
    assert mode.input_requirements.min_sentences == 3


def test_furnace_mode_requires_ideas():
    mode = load_mode(MODES_DIR / "furnace.yaml")
    assert mode.input_requirements.require_ideas_count == 3


def test_executor_mode_has_no_restrictions():
    mode = load_mode(MODES_DIR / "executor.yaml")
    assert len(mode.behaviors.forbidden) == 0
    assert len(mode.output_validation.deny_patterns) == 0
    assert len(mode.output_validation.require_patterns) == 0
    assert mode.metacognitive.checkpoint_interval == 0


def test_forge_mode_has_metacognitive_checkpoints():
    mode = load_mode(MODES_DIR / "forge.yaml")
    assert mode.metacognitive.checkpoint_interval == 5
    assert len(mode.metacognitive.prompts) > 0
    assert mode.metacognitive.session_end_prompt


def test_mode_transitions():
    modes = load_all_modes(MODES_DIR)
    for mode_id, mode in modes.items():
        # Every mode should be reachable from at least one other mode
        if mode_id != "executor":
            assert len(mode.transitions.allowed_from) > 0


def test_load_system_prompt():
    mode = load_mode(MODES_DIR / "forge.yaml")
    base_dir = Path(__file__).parent.parent
    prompt = mode.load_system_prompt(base_dir)
    assert "cognitive forcing partner" in prompt.lower()


def test_validate_mode_id():
    assert validate_mode_id("forge") is True
    assert validate_mode_id("anvil") is True
    assert validate_mode_id("furnace") is True
    assert validate_mode_id("executor") is True
    assert validate_mode_id("unknown") is False


def test_load_nonexistent_mode():
    with pytest.raises(FileNotFoundError):
        load_mode("nonexistent.yaml")


def test_load_nonexistent_dir():
    with pytest.raises(FileNotFoundError):
        load_all_modes("nonexistent_dir")
