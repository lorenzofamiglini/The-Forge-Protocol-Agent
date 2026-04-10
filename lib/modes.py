"""Load and validate mode definitions from YAML files."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml


@dataclass
class DenyPattern:
    id: str
    pattern: str
    reason: str


@dataclass
class RequirePattern:
    id: str
    pattern: str
    reason: str


@dataclass
class OutputValidation:
    deny_patterns: list[DenyPattern] = field(default_factory=list)
    require_patterns: list[RequirePattern] = field(default_factory=list)


@dataclass
class InputRequirements:
    min_sentences: int = 0
    require_draft: bool = False
    require_ideas_count: int = 0


@dataclass
class Metacognitive:
    checkpoint_interval: int = 0
    prompts: list[str] = field(default_factory=list)
    session_end_prompt: str = ""


@dataclass
class Transitions:
    allowed_from: list[str] = field(default_factory=list)
    allowed_to: list[str] = field(default_factory=list)
    confirm_switch: bool = False


@dataclass
class Behaviors:
    required: list[str] = field(default_factory=list)
    forbidden: list[str] = field(default_factory=list)


@dataclass
class Mode:
    id: str
    name: str
    description: str
    system_prompt_file: str
    behaviors: Behaviors
    input_requirements: InputRequirements
    output_validation: OutputValidation
    metacognitive: Metacognitive
    transitions: Transitions = field(default_factory=Transitions)

    def load_system_prompt(self, base_dir: str | Path) -> str:
        """Load the system prompt markdown file relative to base_dir."""
        base = Path(base_dir).resolve()
        path = (base / self.system_prompt_file).resolve()
        try:
            path.relative_to(base)
        except ValueError:
            raise ValueError(f"system_prompt_file escapes base directory: {self.system_prompt_file!r}")
        if not path.exists():
            raise FileNotFoundError(f"System prompt file not found: {path}")
        return path.read_text(encoding="utf-8")


def _parse_patterns(raw: list[dict], cls):
    return [cls(id=p["id"], pattern=p["pattern"], reason=p["reason"]) for p in raw]


def load_mode(path: str | Path) -> Mode:
    """Load a single mode definition from a YAML file."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Mode file not found: {path}")

    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if not isinstance(data, dict):
        raise ValueError(f"Invalid mode file (expected mapping): {path}")

    for key in ("id", "name", "description", "system_prompt_file", "behaviors"):
        if key not in data:
            raise ValueError(f"Mode file missing required key '{key}': {path}")

    behaviors_raw = data.get("behaviors", {})
    behaviors = Behaviors(
        required=behaviors_raw.get("required", []),
        forbidden=behaviors_raw.get("forbidden", []),
    )

    input_raw = data.get("input_requirements", {})
    input_req = InputRequirements(
        min_sentences=input_raw.get("min_sentences", 0),
        require_draft=input_raw.get("require_draft", False),
        require_ideas_count=input_raw.get("require_ideas_count", 0),
    )

    output_raw = data.get("output_validation", {})
    output_val = OutputValidation(
        deny_patterns=_parse_patterns(output_raw.get("deny_patterns", []), DenyPattern),
        require_patterns=_parse_patterns(output_raw.get("require_patterns", []), RequirePattern),
    )

    meta_raw = data.get("metacognitive", {})
    metacognitive = Metacognitive(
        checkpoint_interval=meta_raw.get("checkpoint_interval", 0),
        prompts=meta_raw.get("prompts", []),
        session_end_prompt=meta_raw.get("session_end_prompt", ""),
    )

    trans_raw = data.get("transitions", {})
    transitions = Transitions(
        allowed_from=trans_raw.get("allowed_from", []),
        allowed_to=trans_raw.get("allowed_to", []),
        confirm_switch=trans_raw.get("confirm_switch", False),
    )

    return Mode(
        id=data["id"],
        name=data["name"],
        description=data["description"],
        system_prompt_file=data["system_prompt_file"],
        behaviors=behaviors,
        input_requirements=input_req,
        output_validation=output_val,
        metacognitive=metacognitive,
        transitions=transitions,
    )


def load_all_modes(modes_dir: str | Path) -> dict[str, Mode]:
    """Load all .yaml mode files from a directory. Returns dict keyed by mode id."""
    modes_dir = Path(modes_dir)
    if not modes_dir.is_dir():
        raise FileNotFoundError(f"Modes directory not found: {modes_dir}")

    modes: dict[str, Mode] = {}
    for path in sorted(modes_dir.glob("*.yaml")):
        if path.name == "schema.yaml":
            continue
        mode = load_mode(path)
        if mode.id in modes:
            raise ValueError(f"Duplicate mode id '{mode.id}' in {path}")
        modes[mode.id] = mode

    return modes


VALID_MODE_IDS = {"forge", "anvil", "furnace", "executor"}


def validate_mode_id(mode_id: str) -> bool:
    """Check if a mode ID is one of the built-in modes."""
    return mode_id in VALID_MODE_IDS
