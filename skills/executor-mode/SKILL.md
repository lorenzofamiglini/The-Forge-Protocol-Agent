---
name: executor-mode
description: Switch to Executor mode — normal AI operation with no cognitive friction. Use for mechanical tasks.
version: 0.1.0
author: Forge Protocol
license: MIT
metadata:
  hermes:
    tags: [forge-protocol, execution, automation, no-friction]
    related_skills: [forge-mode, anvil-mode, crucible-mode, forge-status]
---

# Executor Mode — Standard AI Operation

Switch to Executor mode for **mechanical tasks** that don't require your judgment.

## When to Use

- Formatting, translation, data transformation
- Boilerplate code generation
- Calendar coordination, scheduling
- Summarizing documents you've already read
- Any task where delegation is appropriate

## How It Works

Executor mode is standard AI behavior — no friction, no questioning, no checkpoints. The AI does exactly what you ask.

## Activation

Say `/executor-mode` to switch.

## When NOT to Use

If you catch yourself using Executor mode for tasks that require your voice, judgment, or expertise — switch to Forge, Anvil, or Crucible instead. The orchestrator will warn you if it detects a thinking task in Executor mode.

## Rules

- No input requirements
- No output restrictions
- No metacognitive checkpoints
- Full automation — the AI writes, generates, formats freely

## Research basis

Executor mode is the only context where the **Rams (AI-first) protocol** from Cabitza et al. (2023) is acceptable. Rams causes anchoring and automation bias when judgment is involved — for mechanical tasks those biases are irrelevant because there's no judgment to corrupt. If you catch yourself using Executor for a task that carries your voice (an email, an argument, a design choice), switch modes. Full derivation in [RESEARCH.md](../../RESEARCH.md).
