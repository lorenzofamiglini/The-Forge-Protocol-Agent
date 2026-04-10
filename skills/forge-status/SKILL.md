---
name: forge-status
description: Show current Forge Protocol status — active mode, message count, violations, and audit reminders.
version: 0.1.0
author: Forge Protocol
license: MIT
metadata:
  hermes:
    tags: [forge-protocol, status, dashboard, audit]
    related_skills: [forge-mode, anvil-mode, furnace-mode, forge-audit]
---

# Forge Status

Show a dashboard of your current Forge Protocol state.

## Usage

Say `/forge-status` to see:

- **Current mode** (Forge, Anvil, Furnace, or Executor)
- **Message count** in this session
- **Violation count** (times the AI broke mode rules)
- **Mode history** (which modes you've used and for how long)
- **Audit reminders** (overdue weekly canary, monthly stress test, quarterly dependency audit)
- **Next checkpoint** (messages until next metacognitive prompt)

## How to Check

Call the `forge_get_state` tool to retrieve the full state, then display it in a readable format.

## Interpreting Results

- **High violation count** → The AI is struggling to stay in mode. Consider reinforcing the SOUL.md.
- **Heavy executor usage** → You may be delegating thinking tasks. Try switching to Forge mode.
- **Overdue audits** → Time to test your unassisted skills. Run `/forge-audit`.
