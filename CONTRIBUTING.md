# Contributing to Forge Protocol

Thanks for your interest in making AI work *with* human thinking instead of replacing it.

## Ways to Contribute

### New Modes
Drop a YAML file in `modes/` and a system prompt in `souls/`. See `modes/forge.yaml` for the format. Ideas:
- **Mentor Mode** — for tutoring specific subjects
- **Debate Mode** — structured argument practice
- **Code Review Mode** — critique code without rewriting it

### Adapters
Integrate Forge Protocol with other AI tools (Cursor, Aider, VS Code, etc.). The `lib/` module is standalone Python — import and use it anywhere.

### Research
If you're studying AI's effect on human skills, we'd love to collaborate. The audit system (`lib/audit.py`) is designed for longitudinal skill tracking.

## Development Setup

```bash
git clone https://github.com/lorenzofamiglini/The-Forge-Protocol-Agent.git
cd forge-protocol
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest
```

## Code Style
- Python 3.11+ with type hints
- Tests for all new functionality
- Keep `lib/` free of Hermes dependencies (portable core)

## Pull Requests
- One feature per PR
- Include tests
- Update mode YAML schema if adding new fields
