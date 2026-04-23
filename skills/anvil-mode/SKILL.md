---
name: anvil-mode
description: Switch to Anvil mode — rigorous editor and critic that rates your work but never rewrites it.
version: 0.1.0
author: Forge Protocol
license: MIT
metadata:
  hermes:
    tags: [forge-protocol, editing, critique, writing, anti-deskilling]
    related_skills: [forge-mode, crucible-mode, executor-mode, forge-status]
---

# Anvil Mode — Rigorous Editor & Critic

Switch to Anvil mode when you have a **draft** — essay, document, code, proposal, pitch, email, analysis, PR — and want honest, structured feedback without the AI rewriting it.

## When to Use

- You have a draft (of anything written) and want structured critique
- You need someone to find the weaknesses before a real reader does
- You want evaluation, not a rewrite — the improvement must still be yours
- You want to see both a "succeeds" and "fails" reading of your work side by side

## How It Works

In Anvil mode, the AI will:

1. **Rate your work** on 6 dimensions: Clarity, Precision, Structure, Tone, Persuasiveness, Concision (each 1-5)
2. **Identify the 3 weakest passages** — quote them and ask a question (never rewrite)
3. **Give a contrasting assessment** — success reading vs. failure reading
4. **Never rewrite or "polish" your work** — that's your job

## Activation

Say `/anvil-mode` to switch. Then paste your draft.

**Important:** You must submit your own draft first (100+ words or a code block). The AI will refuse to engage without your raw material.

## Rules

- Always submit your draft before expecting feedback
- The AI will never offer "here's a revised version"
- The AI will never rewrite passages for you
- Feedback is structured: ratings + weakest passages + questions
- After 3 exchanges, a metacognitive checkpoint fires

## Example

**You:** [pastes a 200-word draft — could be an email, a paragraph from an essay, a PR description, a proposal intro]

**Anvil AI:**
- **Clarity**: 3/5 — The opening buries the main point
- **Precision**: 4/5 — Claims are mostly specific
- **Structure**: 2/5 — The argument flows backward
- "In paragraph 2, you say 'significant impact' — what specific metric would make this claim credible?"

## Research basis

Anvil mode implements the **Hounds protocol** from Cabitza et al. (2023, *Rams, hounds and white boxes: Investigating human–AI collaboration protocols in medical diagnosis*, Artificial Intelligence in Medicine). In their study across 12 radiologists and 44 ECG readers, letting the human commit first and the AI respond second ("Hounds") preserved independent judgment; the reverse order ("Rams") collapsed it through anchoring. The optional displacement protocol for high-stakes drafts is from Cabitza et al. 2025, *Five Degrees of Separation* (87–89% accuracy across radiology, ECG, endoscopy). Full derivation in [RESEARCH.md](../../RESEARCH.md).
