"""Tests for mode loading and validation."""

from pathlib import Path

import pytest

from lib.modes import VALID_MODE_IDS, Mode, load_all_modes, load_mode

MODES_DIR = Path(__file__).parent.parent / "modes"


def test_load_all_modes():
    modes = load_all_modes(MODES_DIR)
    assert len(modes) == 4
    assert set(modes.keys()) == {"forge", "anvil", "crucible", "executor"}


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


def test_forge_mode_has_input_rules():
    mode = load_mode(MODES_DIR / "forge.yaml")
    assert len(mode.input_rules) > 0


def test_anvil_mode_has_input_rules():
    mode = load_mode(MODES_DIR / "anvil.yaml")
    assert len(mode.input_rules) > 0
    assert any("draft" in rule.lower() for rule in mode.input_rules)


def test_crucible_mode_has_input_rules():
    mode = load_mode(MODES_DIR / "crucible.yaml")
    assert len(mode.input_rules) > 0
    assert any("3" in rule or "ideas" in rule.lower() for rule in mode.input_rules)


def test_executor_mode_has_no_restrictions():
    mode = load_mode(MODES_DIR / "executor.yaml")
    assert len(mode.behaviors.forbidden) == 0
    assert len(mode.input_rules) == 0
    assert mode.metacognitive.checkpoint_interval == 0


def test_forge_mode_has_metacognitive_checkpoints():
    mode = load_mode(MODES_DIR / "forge.yaml")
    assert mode.metacognitive.checkpoint_interval == 5
    assert len(mode.metacognitive.prompts) > 0
    assert mode.metacognitive.session_end_prompt


def test_mode_transitions():
    modes = load_all_modes(MODES_DIR)
    for mode_id, mode in modes.items():
        if mode_id != "executor":
            assert len(mode.transitions.allowed_from) > 0


def test_load_system_prompt():
    mode = load_mode(MODES_DIR / "forge.yaml")
    base_dir = Path(__file__).parent.parent
    prompt = mode.load_system_prompt(base_dir)
    assert "cognitive forcing partner" in prompt.lower()


def test_valid_mode_ids_set():
    assert VALID_MODE_IDS == {"forge", "anvil", "crucible", "executor"}
    assert "unknown" not in VALID_MODE_IDS


def test_load_nonexistent_mode():
    with pytest.raises(FileNotFoundError):
        load_mode("nonexistent.yaml")


def test_load_nonexistent_dir():
    with pytest.raises(FileNotFoundError):
        load_all_modes("nonexistent_dir")
