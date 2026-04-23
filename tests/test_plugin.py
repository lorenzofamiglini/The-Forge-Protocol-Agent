"""Tests for the Hermes Agent plugin integration."""

import json
import sys
from pathlib import Path

import pytest

# Ensure hermes-agent is importable
HERMES_REPO = Path(__file__).parent.parent.parent / "hermes-agent"
if HERMES_REPO.exists() and str(HERMES_REPO) not in sys.path:
    sys.path.insert(0, str(HERMES_REPO))

# Ensure our repo root is importable
REPO_ROOT = Path(__file__).parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from plugin import (
    _handle_validate_input,
    _handle_validate_output,
    _handle_checkpoint,
    _handle_get_state,
    _handle_set_mode,
    _handle_log,
)


def _call(handler, args=None):
    """Call a tool handler and parse JSON result."""
    return json.loads(handler(args or {}))


class TestValidateInputTool:
    def test_anvil_returns_input_rules(self):
        result = _call(_handle_validate_input, {"user_input": "fix this", "mode": "anvil"})
        assert result["mode"] == "anvil"
        assert len(result["input_rules"]) > 0
        assert any("draft" in r.lower() for r in result["input_rules"])

    def test_executor_returns_no_rules(self):
        result = _call(_handle_validate_input, {"user_input": "hi", "mode": "executor"})
        assert result["mode"] == "executor"
        assert len(result["input_rules"]) == 0

    def test_invalid_mode(self):
        result = _call(_handle_validate_input, {"user_input": "test", "mode": "nonexistent"})
        assert "error" in result


class TestValidateOutputTool:
    def test_forge_returns_behavioral_rules(self):
        result = _call(_handle_validate_output, {
            "response": "test response",
            "mode": "forge",
        })
        assert result["mode"] == "forge"
        assert len(result["required_behaviors"]) > 0
        assert len(result["forbidden_behaviors"]) > 0

    def test_executor_returns_no_forbidden(self):
        result = _call(_handle_validate_output, {
            "response": "test response",
            "mode": "executor",
        })
        assert result["mode"] == "executor"
        assert len(result["forbidden_behaviors"]) == 0


class TestSetModeTool:
    def test_switch_to_forge(self):
        result = _call(_handle_set_mode, {"mode": "forge"})
        assert result["current"] == "forge"

    def test_invalid_mode(self):
        result = _call(_handle_set_mode, {"mode": "invalid"})
        assert "error" in result

    def test_switch_to_same_mode(self):
        _call(_handle_set_mode, {"mode": "executor"})
        result = _call(_handle_set_mode, {"mode": "executor"})
        assert result["changed"] is False


class TestGetStateTool:
    def test_returns_state(self):
        result = _call(_handle_get_state)
        assert "current_mode" in result
        assert "message_count" in result
        assert "violation_count" in result
        assert "audit_reminders" in result


class TestCheckpointTool:
    def test_returns_checkpoint_status(self):
        result = _call(_handle_checkpoint)
        assert "due" in result
        assert "messages_until_next" in result


class TestLogTool:
    def test_log_interaction(self):
        result = _call(_handle_log)
        assert result["logged"] is True
        assert "message_count" in result

    def test_log_with_violation(self):
        result = _call(_handle_log, {
            "violation_type": "output",
            "rule_id": "direct-answer",
            "message": "Gave a direct answer in forge mode",
        })
        assert result["logged"] is True
        assert result["violation_logged"] is True


class TestHermesRegistration:
    """Test that the plugin registers correctly with Hermes PluginManager."""

    @pytest.fixture(autouse=True)
    def skip_if_no_hermes(self):
        try:
            from tools.registry import registry
            from hermes_cli.plugins import PluginManager, PluginManifest, PluginContext
        except ImportError:
            pytest.skip("hermes-agent not installed")

    def test_registers_all_tools(self):
        from tools.registry import ToolRegistry
        from hermes_cli.plugins import PluginManager, PluginManifest, PluginContext
        from plugin import register

        # Fresh registry for isolation
        fresh_registry = ToolRegistry()

        # Monkey-patch temporarily
        import tools.registry as reg_mod
        original = reg_mod.registry
        reg_mod.registry = fresh_registry

        try:
            manifest = PluginManifest(name="forge-protocol", source="test")
            manager = PluginManager()
            ctx = PluginContext(manifest, manager)
            register(ctx)

            forge_tools = [n for n in fresh_registry.get_all_tool_names() if n.startswith("forge_")]
            assert set(forge_tools) == {
                "forge_validate_input", "forge_validate_output",
                "forge_checkpoint", "forge_get_state", "forge_set_mode",
                "forge_canary_list", "forge_canary_submit", "forge_log",
            }
        finally:
            reg_mod.registry = original

    def test_registers_3_hooks(self):
        from hermes_cli.plugins import PluginManager, PluginManifest, PluginContext
        from plugin import register

        manifest = PluginManifest(name="forge-protocol", source="test")
        manager = PluginManager()
        ctx = PluginContext(manifest, manager)
        register(ctx)

        assert "on_session_start" in manager._hooks
        assert "on_session_end" in manager._hooks
        assert "pre_tool_call" in manager._hooks
