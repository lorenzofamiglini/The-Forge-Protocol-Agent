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
- Writing, analysis, debugging, strategy, or communication task
- 5-10 minute time limit
- Track your comfort level and speed over time
- Purpose: early warning if skills are declining

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

1. Call `forge_get_state` to check audit status
2. Present the appropriate challenge
3. After completion, call `forge_log` to record the audit
4. Compare results to previous audits

## Healthy Targets

- **Mode split**: ~40% Forge/Furnace, ~30% Anvil, ~30% Executor
- **Canary trend**: stable or improving over 4+ weeks
- **Violation rate**: decreasing over time (AI learning to stay in mode)
