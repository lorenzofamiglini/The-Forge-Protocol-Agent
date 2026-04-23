<div align="center">

# Forge Protocol

### The AI that refuses to think for you.

**An open-source framework that rewires how AI responds — so you stay sharp.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Hermes Agent](https://img.shields.io/badge/built%20on-Hermes%20Agent-purple.svg)](https://github.com/NousResearch/hermes-agent)
[![Research paper](https://img.shields.io/badge/paper-RESEARCH.md-8A2BE2.svg)](RESEARCH.md)

[Quick Start](#quick-start) | [Why This Exists](#why-this-exists) | [The 4 Modes](#the-4-modes) | [Measure Your Sovereignty](#measure-your-cognitive-sovereignty) | [For Educators](#for-schools--universities) | [Architecture](#architecture)

</div>

---

## The Problem

A [2024 Wharton/PNAS study](https://www.pnas.org/) found that **workers who used AI became 17% worse** at doing tasks independently — after just one week. The more they relied on AI, the less they could think without it.

This isn't a bug. It's the default behavior of every AI assistant: you ask, it answers, your skills atrophy.

**Forge Protocol changes the default.**

Instead of giving you answers, it gives you **better questions**. Instead of writing your email, it **critiques your draft**. Instead of generating ideas, it **stress-tests yours**.

> "The goal is not to slow you down. It's to keep you in the driver's seat of your own thinking."

---

## Why This Exists

Every AI tool today optimizes for one thing: **get the human to the answer as fast as possible**. That's great for productivity. It's terrible for learning.

Research calls this **deskilling** — the gradual erosion of human capabilities through automation:

| Study | Finding |
|-------|---------|
| Wharton/PNAS RCT (2024) | 17% performance decline after AI assistance removed |
| Cabitza et al. (2024) | Identified 4 types: cognitive, semiotic, social, moral deskilling |
| Bjork & Bjork (1994) | "Desirable difficulties" — productive struggle improves long-term retention |
| Parasuraman & Manzey (2010) | Automation complacency: humans stop verifying AI output after ~3 interactions |

Forge Protocol is built on a simple idea from cognitive science: **the brain that struggles is the brain that learns**. The full theoretical derivation, including the generation effect, desirable difficulties, automation complacency, and the XAI halo effect, is in [RESEARCH.md](RESEARCH.md) and the paper under [`docs/forge-protocol-paper.tex`](docs/forge-protocol-paper.tex).

---

## The 4 Modes

<table>
<tr>
<td width="25%" align="center">

### Forge

**Thinking Partner**

Asks questions.
Never gives answers.
Forces you to reason.

`/forge-mode`

</td>
<td width="25%" align="center">

### Anvil

**Editor / Critic**

Rates your draft.
Finds weaknesses.
Never rewrites.

`/anvil-mode`

</td>
<td width="25%" align="center">

### Crucible

**Idea Stress-Tester**

Steelmans, then attacks.
Maps blind spots.
Never fills gaps.

`/crucible-mode`

</td>
<td width="25%" align="center">

### Executor

**Normal AI**

Full automation.
No friction.
For mechanical tasks only.

`/executor-mode`

</td>
</tr>
</table>

### How They Work

**Forge mode** — You say "Help me plan my thesis." The AI responds: *"What's your central claim? Not the topic — the argument. What would someone who disagrees say?"* It never writes for you.

**Anvil mode** — You paste your draft email. The AI rates it on 6 dimensions (clarity, precision, structure, tone, persuasiveness, concision), quotes the 3 weakest passages, and asks *"Where do you disagree with my assessment?"* It never offers rewrites.

**Crucible mode** — You bring 3 ideas. The AI steelmans each one (strongest possible version), then attacks it (finds the fatal flaw). It maps what you haven't considered. It never suggests new ideas.

**Executor mode** — Formatting, translation, boilerplate, scheduling. Tasks that don't require your judgment. No friction, no questions.

### Automatic Task Detection

The orchestrator SOUL classifies every message as a **thinking task** or an **execution task** inline — no extra tool call, no regex. If you're in Executor mode but send a thinking task ("help me write this important email"), the system warns you. No more accidental delegation.

---

## Measure Your Cognitive Sovereignty

Most "anti-AI-dependency" tools are aspirational — they *tell* you to use AI less. Forge Protocol actually measures whether your independent skills are improving, flat, or drifting down.

### The adversarial auditor

The original design had one flaw: it asked the *same* LLM that generated a response to judge whether the response followed the mode rules. LLMs rubber-stamp themselves. Fixed:

- Set `FORGE_AUDITOR_ENABLED=1` and the `forge_validate_input` / `forge_validate_output` tools route through an **independent Claude Sonnet instance** that judges compliance, quotes violations verbatim, and returns structured JSON the orchestrator treats as ground truth.
- The auditor runs on its own config (`FORGE_AUDITOR_MODEL`, `FORGE_AUDITOR_BACKEND`, Vertex or direct API) so you can run the primary LLM and the auditor on different models, different accounts, or even different providers.

### The canary — real skill tracking, not reminders

A fixed set of prompts (writing, analysis, debugging, strategy, communication) with stable IDs. You answer one unassisted, the auditor scores it, and the result is stored across weeks so you can see the trend.

```
/forge-audit weekly
# → prompt shown, 5-minute timer
# → you submit your unassisted answer
# → auditor returns:
  clarity: 4    depth: 3    independence: 5     overall: 4.0
  change vs. previous: +0.3   mean of last 5: 3.8   slope: +0.15/attempt
```

If the slope is flat or negative after a few weeks, the framework is failing you — and you'll hear that honestly instead of a "great job!" from a sycophantic model.

| What it tracks | What the number means |
|---|---|
| **Clarity** (1-5) | Specific, readable, no filler hedging |
| **Depth** (1-5) | Genuine reasoning, not templated surface |
| **Independence** (1-5) | Your voice, not pasted AI patterns |
| **Slope per attempt** | Linear trend across your full canary history |

Storage lives at `~/.forge-state/canary_history.json`. Nothing leaves your machine except the single auditor API call that returns a score.

---

## Quick Start

### Prerequisites
- Python 3.11+
- [Hermes Agent](https://github.com/NousResearch/hermes-agent)
- An LLM provider (Vertex AI, OpenRouter, Anthropic API, etc.)

### Install

```bash
# Clone
git clone https://github.com/lorenzofamiglini/The-Forge-Protocol-Agent.git
cd forge-protocol

# Set up Python environment
python3 -m venv .venv
source .venv/bin/activate
pip install -e .

# Install Hermes Agent (if not already installed)
pip install hermes-agent

# Install the Forge Protocol plugin into Hermes
./install.sh
```

### Configure your LLM

```bash
# Option A: Google Cloud Vertex AI (Claude)
export VERTEX_PROJECT=your-project-id
export VERTEX_REGION=us-east5

# Option B: Anthropic API directly
export ANTHROPIC_API_KEY=your-key

# Option C: OpenRouter (access to 100+ models)
export OPENROUTER_API_KEY=your-key
```

### Launch

```bash
# Start Hermes with Forge Protocol
./forge.sh

# Or manually
hermes
```

Then try:
```
/forge-mode
Help me think through my thesis on AI in education.
```

---

## For Schools & Universities

Forge Protocol was built with education in mind. It turns any LLM into a **Socratic tutor** that strengthens student thinking instead of replacing it.

### The Problem in Education
- Students paste assignments into ChatGPT and submit the output
- Writing skills decline because the AI writes for them
- Critical thinking atrophies because the AI thinks for them
- Students can't tell the difference between understanding and having access to answers

### How Forge Protocol Helps

| Without Forge | With Forge |
|---------------|------------|
| Student: "Write my essay on climate policy" | Student: "Write my essay on climate policy" |
| AI: *writes a complete essay* | AI: *"What's your thesis? What evidence supports it? What's the strongest counterargument?"* |
| Student learns: nothing | Student learns: how to build an argument |

### Deployment Options

1. **Individual students** — Install locally, use for study sessions and paper writing
2. **Course-level** — Instructor provides a Forge Protocol instance, students use it as a thinking partner
3. **Institution-level** — Deploy via Hermes Agent with Vertex AI backend, enforce Forge mode for academic work
4. **Research** — Use the audit system to measure skill progression over time

### Self-Audit System

The **measurable** part of the framework — see [Measure Your Cognitive Sovereignty](#measure-your-cognitive-sovereignty) above for the full write-up. Three cadences:
- **Weekly canary** — Timed unassisted challenge. Auditor scores it on clarity, depth, and independence. Compared across weeks.
- **Monthly stress test** — Extended unassisted work. Compared to your AI-assisted baseline.
- **Quarterly dependency audit** — Mode usage analysis. Catches "living in Executor mode."

---

## Architecture

```
You (CLI / Telegram / Discord / Slack)
  |
  v
Hermes Agent + Forge Orchestrator SOUL
  |
  |-- [SOUL classifies inline] → thinking or execution?
  |-- forge_set_mode    → switch to appropriate mode
  |-- forge_validate_input  → does input meet mode requirements?
  |
  |-- Forge sub-agent   → Socratic questions only
  |-- Anvil sub-agent   → critique only, never rewrite
  |-- Crucible sub-agent → stress-test only, never fill gaps
  |-- Executor          → normal AI, no restrictions
  |
  |-- forge_validate_output → did response follow mode rules?
  |-- forge_checkpoint      → metacognitive prompt if due
  |-- forge_log             → audit trail
  |
  v
Validated Response → You
```

### Project Structure

```
forge-protocol/
├── plugin/          # Hermes Agent plugin (6 tools + 3 hooks)
│   ├── plugin.yaml
│   └── __init__.py
├── lib/             # Pure Python core (no Hermes dependency)
│   ├── modes.py     # YAML mode loader
│   ├── state.py     # Session state management
│   ├── validator.py # Validation rule retrieval for LLM evaluation
│   ├── checkpoints.py # Metacognitive checkpoint scheduler
│   └── audit.py     # Self-audit system
├── modes/           # Portable YAML mode definitions
│   ├── forge.yaml
│   ├── anvil.yaml
│   ├── crucible.yaml
│   └── executor.yaml
├── souls/           # System prompts (Hermes SOUL.md format)
│   ├── forge-orchestrator.md
│   ├── forge.md
│   ├── anvil.md
│   ├── crucible.md
│   └── executor.md
├── skills/          # Hermes slash commands (/forge-mode, etc.)
├── tests/           # Unit tests
├── install.sh       # One-line installer for Hermes
└── forge.sh         # Launch script
```

### Key Design Choices

- **Portable core** — `lib/` has zero Hermes dependency. Use it in any Python project.
- **YAML-driven modes** — Add custom modes by dropping a YAML file. No code changes.
- **Plugin architecture** — Registers via Hermes's native `PluginContext` API.
- **File-based state** — JSON session files in `~/.forge-state/`. No database required.
- **LLM-native classification** — The orchestrator SOUL classifies tasks inline. No regex, no extra tool call.

---

## Create Your Own Mode

Drop a YAML file in `modes/`:

```yaml
id: mentor
name: "Mentor Mode"
description: "Guides through problems step by step, never gives the answer"

system_prompt_file: "souls/mentor.md"

behaviors:
  required:
    - "Break problems into sub-problems"
    - "Ask the student to solve each sub-problem"
    - "Every response must contain at least one question"
  forbidden:
    - "Give the final answer directly"
    - "Skip steps in the reasoning"

input_rules:
  - "Student must attempt the problem before receiving guidance"

metacognitive:
  checkpoint_interval: 3
  prompts:
    - "Can you explain what we've figured out so far in your own words?"
```

---

## The Research

Forge Protocol is grounded in peer-reviewed cognitive science:

- **Generation Effect** (Slamecka & Graf, 1978) — Information you generate yourself is retained better than information you passively receive
- **Desirable Difficulties** (Bjork & Bjork, 1994) — Productive struggle during learning leads to better long-term retention
- **Automation Complacency** (Parasuraman & Manzey, 2010) — Humans stop verifying automated output after initial trust is established
- **Deskilling Taxonomy** (Cabitza et al., 2024) — Four types: cognitive (can't think), semiotic (can't interpret), social (can't collaborate), moral (can't judge)
- **AI-Induced Skill Decline** (Dell'Acqua et al., 2024) — Wharton RCT showing 17% decline in unassisted performance after AI use
- **Judicial AI Paradigm** — Present both sides of every issue, never converge to a single recommendation
- **Frictional AI** — Programmed inefficiencies that force engagement over passive consumption

---

## Built On

Forge Protocol is built as a native plugin for [**Hermes Agent**](https://github.com/NousResearch/hermes-agent) by [Nous Research](https://nousresearch.com/) — an open-source AI agent framework with multi-LLM support, sub-agent delegation, skills system, and 14+ messaging gateways.

Hermes Agent provides the orchestration backbone: SOUL.md personality injection, tool registration via `PluginContext`, session persistence with SQLite + FTS5, and support for 18+ LLM providers including Vertex AI, OpenRouter, Anthropic, and local models.

**Huge thanks to the Nous Research team** for building such a solid open-source foundation.

---

## Contributing

Forge Protocol is open source (MIT). We welcome:

- **New modes** — Custom YAML mode definitions for specific domains (law, medicine, coding)
- **Adapters** — Integrations with Cursor, Aider, VS Code, or other AI tools
- **Research** — Studies measuring the effectiveness of cognitive forcing functions
- **Translations** — Internationalize the system prompts and mode definitions

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

## FAQ

**Q: Doesn't this just make AI slower and more annoying?**
A: In Forge/Anvil/Crucible modes, yes — intentionally. That friction is the feature. When you need speed, switch to Executor mode. The protocol distinguishes between tasks that need your brain and tasks that don't.

**Q: Can I use this without Hermes Agent?**
A: Yes. The `lib/` directory is a standalone Python library with zero dependencies beyond PyYAML. Import `get_input_rules()` and `get_output_rules()` to retrieve the natural-language rules for a mode, then have your own LLM evaluate compliance. The SOUL files in `souls/` can be copy-pasted into any LLM's system prompt.

**Q: What LLMs does this work with?**
A: Any LLM supported by Hermes Agent — Claude (via Vertex AI or API), GPT-4, Gemini, Llama, Mistral, and 100+ models via OpenRouter.

**Q: Is this just a system prompt?**
A: The system prompts (`souls/`) are the starting point, but Forge Protocol adds enforcement: input validation (did the student submit their own work?), output validation (did the AI follow mode rules?), metacognitive checkpoints (periodic "are you still thinking?" prompts), inline task classification (warning when delegating thinking tasks), and a self-audit system. All validation is LLM-native — the orchestrator evaluates compliance using natural language rules, not regex.

---

<div align="center">

**Stop outsourcing your thinking.**

[Get Started](#quick-start) | [Star this repo](https://github.com/lorenzofamiglini/The-Forge-Protocol-Agent)

---

## Author

Created by **Lorenzo Famiglini** (lorenzofamiglini@gmail.com)

Built on [Hermes Agent](https://github.com/NousResearch/hermes-agent) by [Nous Research](https://nousresearch.com/).

</div>
