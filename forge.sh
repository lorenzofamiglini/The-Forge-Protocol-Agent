#!/usr/bin/env bash
# Launch Forge Protocol via Hermes Agent
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Activate venv if it exists
if [ -d "$SCRIPT_DIR/.venv" ]; then
    source "$SCRIPT_DIR/.venv/bin/activate"
fi

# Check required env vars for Vertex AI (optional — other providers work too)
if [ -n "${VERTEX_PROJECT:-}" ]; then
    export VERTEX_PROJECT
    export VERTEX_REGION="${VERTEX_REGION:-us-east5}"
fi

echo "Forge Protocol — The AI that refuses to think for you."
echo ""
echo "  Commands: /forge-mode  /anvil-mode  /crucible-mode  /executor-mode"
echo "            /forge-status  /forge-audit"
echo ""

# Launch Hermes interactive CLI
exec hermes "$@"
