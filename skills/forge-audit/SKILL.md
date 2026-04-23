---
name: forge-audit
description: Run Forge Protocol self-audits — weekly canary, monthly stress test, or quarterly dependency review.
version: 0.1.0
author: Forge Protocol
license: MIT
metadata:
  hermes:
    tags: [forge-protocol, audit, self-assessment, skills]
    related_skills: [forge-status, forge-mode]
---

# Forge Audit — Self-Assessment System

Test your unassisted skills to prevent AI dependency from eroding your capabilities.

## Audit Types

### Weekly Canary (`/forge-audit weekly`)

A timed challenge you complete **without AI assistance**:
- A fixed set of writing, analysis, debugging, strategy, and communication prompts (stable IDs so you take the same one repeatedly)
- 5-10 minute time limit
- Your answer is scored by an independent Claude Sonnet auditor on clarity, depth, and independence
- Scores are stored across weeks — you see trend, change vs. previous, mean of last 5, linear slope
- Purpose: measure, not just remind. If your independence score drifts down, the canary catches it before you do.

### Monthly Stress Test (`/forge-audit monthly`)

A harder challenge requiring sustained unassisted work:
- Complete a significant task without AI for 30-60 minutes
- Compare output quality to your AI-assisted baseline
- Purpose: verify you can still perform under pressure

### Quarterly Dependency Audit (`/forge-audit quarterly`)

Review your AI usage patterns across all sessions:
- Mode ratios (are you living in Executor mode?)
- Violation trends (is the AI breaking mode rules more often?)
- Skill progression (are canary scores improving or declining?)
- Purpose: macro-level view of your cognitive sovereignty

## How It Works

1. Call `forge_get_state` to check audit status and which audits are overdue
2. For a weekly canary: call `forge_canary_list` to show the user the fixed prompts (or pick one by id), present the challenge, and enforce the time limit by prompting the user to commit before submitting
3. Submit the user's unassisted response via `forge_canary_submit(prompt_id, response)` — the adversarial auditor (Claude Sonnet) scores it and returns the full trend
4. Show the user their last score, change vs. previous, and slope across attempts — be honest about what the data says

## Healthy Targets

- **Mode split**: ~40% Forge/Crucible, ~30% Anvil, ~30% Executor
- **Canary trend**: stable or improving over 4+ weeks
- **Violation rate**: decreasing over time (AI learning to stay in mode)
