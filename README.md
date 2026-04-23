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

Research calls this **deskilling** — the gradual erosion of human capabilities through automation. Forge Protocol's design is lifted directly from the empirical programme run by Federico Cabitza's lab at Milano-Bicocca, which has spent a decade showing *how* AI deskills users and *which interaction patterns* prevent it:

| Study | Finding |
|-------|---------|
| Dell'Acqua et al., Wharton/PNAS RCT (2024) | 17% performance decline after AI assistance removed |
| Cabitza et al. (2023) — *Rams, hounds and white boxes*, Artificial Intelligence in Medicine | Human-first "Hounds" ordering preserved independent judgment; AI-first "Rams" collapsed it through anchoring (12 radiologists + 44 ECG readers) |
| Cabitza et al. (2024) — xAI 2024 Best Paper | **White-box paradox** — articulate AI explanations *increase* uncritical acceptance rather than decrease it |
| Cabitza et al. (2025) — *Five Degrees of Separation* | Displacement protocol (human and AI work independently then combine) reaches 87–89% accuracy across radiology, ECG, endoscopy |
| Natali, Marconi, Dias Duran, Miglioretti & Cabitza (2025) | Four deskilling types: cognitive, semiotic, social, moral — plus **epistemic sclerosis** at team level |
| Famiglini et al. (2024) — *Never tell me the odds*, AI in Medicine Vol 150 | **Pro-hoc explanations** (commitment before explanation) prevent anchoring that post-hoc explanations cause |
| Doshi & Hauser (2024) | AI-assisted creative outputs are **5% more similar to each other** than human-only outputs — convergence as a measurable deskilling signal |
| Bjork & Bjork (1994); Parasuraman & Manzey (2010) | "Desirable difficulties" and automation-complacency thresholds — cognitive-science foundations |

> **Forge Protocol doesn't cite these papers — it implements them.** The four modes map one-to-one onto protocols empirically validated in the Cabitza lab: Forge = judicial AI paradigm, Anvil = Hounds, Crucible = frictional AI + programmed inefficiencies, Executor = Rams (the only context where AI-first is acceptable). The project's maintainer, Lorenzo Famiglini, is a co-author on the Cabitza lab's XAI-design and conformal-prediction work that these patterns draw from. See [RESEARCH.md](RESEARCH.md) for the full mapping.

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

*Judicial AI paradigm<br>(Cabitza et al. 2025)*

</td>
<td width="25%" align="center">

### Anvil

**Editor / Critic**

Rates your draft.
Finds weaknesses.
Never rewrites.

`/anvil-mode`

*Hounds protocol<br>(Cabitza et al. 2023)*

</td>
<td width="25%" align="center">

### Crucible

**Idea Stress-Tester**

Steelmans, then attacks.
Maps blind spots.
Never fills gaps.

`/crucible-mode`

*Frictional AI<br>(Cabitza et al. 2024)*

</td>
<td width="25%" align="center">

### Executor

**Normal AI**

Full automation.
No friction.
For mechanical tasks only.

`/executor-mode`

*Rams protocol<br>(only here)*

</td>
</tr>
</table>

### How They Work

**Forge mode** (*Judicial AI*) — You say "Help me plan my thesis." The AI presents the case FOR and AGAINST your angle in parallel, then asks *"What's your central claim? What would someone who disagrees say?"* It never converges to a single recommendation (OMA principle: Open, Multiple, Adjunct).

**Anvil mode** (*Hounds protocol*) — You paste your draft. **The order matters**: you commit first (by submitting your full draft), the AI responds second. This is what Cabitza's 2023 study found preserved independent judgment. The AI rates on 6 dimensions, quotes the 3 weakest passages, and asks *"Where do you disagree with my assessment?"* It never rewrites.

**Crucible mode** (*Frictional AI*) — You bring **3+ ideas** (the mode refuses fewer). The AI steelmans each, attacks, and maps what you haven't considered. An epistemic-sclerosis guard kicks in if your ideas read as generic — the mode will ask for one wild or contrarian idea to stop premature convergence before pressure-testing.

**Executor mode** (*Rams protocol*) — Formatting, translation, boilerplate, scheduling. No friction, no questions. This is the only mode where the AI-first pattern is acceptable — Cabitza's research shows Rams causes anchoring when *judgment* is at stake, so the orchestrator warns you if it detects a thinking task here.

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
├── plugin/          # Hermes Agent plugin (9 tools + 2 hooks)
│   ├── plugin.yaml
│   └── __init__.py
├── lib/             # Pure Python core (no Hermes dependency)
│   ├── modes.py        # YAML mode loader
│   ├── state.py        # Session state management
│   ├── validator.py    # Validation rule retrieval for LLM evaluation
│   ├── auditor.py      # Adversarial Sonnet auditor (optional, opt-in)
│   ├── canary.py       # Fixed canary prompts + skill tracking
│   ├── checkpoints.py  # Metacognitive checkpoint scheduler
│   └── audit.py        # Weekly/monthly/quarterly audit reminders
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
├── docs/            # Research paper (LaTeX source)
├── tests/           # Unit tests (85, pytest)
├── RESEARCH.md      # Theoretical grounding + citations
├── install.sh       # Installer for Hermes (copy by default, --dev for symlink)
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

Forge Protocol is grounded in peer-reviewed cognitive science and the Cabitza lab's decade-long empirical programme on human-AI collaboration. [RESEARCH.md](RESEARCH.md) has the full mapping; the summary:

**Foundational cognitive science:**
- **Generation effect** (Slamecka & Graf, 1978) — self-generated content is retained better than passively consumed content
- **Desirable difficulties** (Bjork & Bjork, 1994) — productive struggle improves long-term retention
- **Cognitive forcing strategies** (Croskerry, 2003) — explicit commitment before consultation activates analytical reasoning
- **Automation complacency** (Parasuraman & Manzey, 2010) — humans stop verifying automated output after initial trust

**Cabitza lab — empirical human-AI collaboration protocols (Milano-Bicocca):**
- **Hounds / Rams / White Boxes** (Cabitza et al., 2023, *Artificial Intelligence in Medicine*) — human-first ordering empirically preserves judgment; AI-first collapses it
- **White-box paradox** (Cabitza et al., 2024 — xAI 2024 Best Paper) — articulate explanations increase automation bias rather than decrease it
- **Frictional AI + programmed inefficiencies** (Cabitza et al., 2019, 2024) — deliberate cognitive challenges prevent automatic reliance
- **Judicial AI paradigm** (Cabitza et al., 2025) — contrasting evidence replaces oracular verdicts
- **OMA — Open, Multiple, Adjunct** (Cabitza et al., 2022) — design principles for decision-support outputs
- **Displacement protocol** (Cabitza et al., 2025 — *Five Degrees of Separation*) — 87–89% accuracy when human and AI work independently then combine
- **Deskilling taxonomy** (Natali, Marconi, Dias Duran, Miglioretti & Cabitza, 2025) — four types: cognitive, semiotic, social, moral + epistemic sclerosis at team level

**Famiglini lab contributions (maintainer's own co-authored work):**
- **Pro-hoc explanations** (Famiglini et al., 2024, *Never tell me the odds*, AI in Medicine Vol 150) — commitments before explanations prevent anchoring
- **Contrasting evidence via CAMs** (Famiglini et al., CD-MAKE 2022; 2024 alternative strategies) — visual dual-evidence forces active adjudication
- **Evidence-based XAI design** — explanations evaluated on understandability + clinical relevance, not plausibility
- **Conformal prediction for ECG** (Famiglini et al., 2025) — uncertainty quantification as commitment-forcing mechanism

**Convergence and the Wharton RCT:**
- **AI-induced convergence** (Doshi & Hauser, 2024) — 5% homogenisation across AI-assisted creative outputs
- **AI-induced skill decline** (Dell'Acqua et al., 2024) — 17% unassisted-performance decline after one week of AI use

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
A: Any LLM supported by Hermes Agent — Claude (via Vertex AI or API), GPT, Gemini, Llama, Mistral, and 100+ models via OpenRouter.

**Q: Is this just a system prompt?**
A: The system prompts (`souls/`) are the starting point, but Forge Protocol adds enforcement: input validation (did the student submit their own work?), output validation (did the AI follow mode rules?), metacognitive checkpoints (periodic "are you still thinking?" prompts), inline task classification (warning when delegating thinking tasks), and a self-audit system. All validation is LLM-native — the orchestrator evaluates compliance using natural language rules, not regex.

---

<div align="center">

**Stop outsourcing your thinking.**

[Get Started](#quick-start) | [Star this repo](https://github.com/lorenzofamiglini/The-Forge-Protocol-Agent)

---

## Author

Created by **Lorenzo Famiglini, PhD** (lorenzofamiglini@gmail.com). Co-author on the Cabitza lab's work on explainable AI in medical decision support, contrasting-evidence class-activation-maps (CD-MAKE 2022; 2024), *Never tell me the odds* (AI in Medicine 2024), and conformal prediction for ECG interpretation (2025). Forge Protocol is a direct implementation of those collaboration protocols, translated from medical decision support to LLM-augmented knowledge work.

Built on [Hermes Agent](https://github.com/NousResearch/hermes-agent) by [Nous Research](https://nousresearch.com/).

</div>
