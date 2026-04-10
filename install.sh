#!/usr/bin/env bash
# Forge Protocol installer for Hermes Agent
# Symlinks plugin, skills, and SOUL into ~/.hermes/
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HERMES_HOME="${HERMES_HOME:-$HOME/.hermes}"

echo "=== Forge Protocol Installer ==="
echo "Repo:        $SCRIPT_DIR"
echo "Hermes home: $HERMES_HOME"
echo ""

# ---------------------------------------------------------------------------
# 1. Check hermes-agent is installed
# ---------------------------------------------------------------------------
if ! command -v hermes &>/dev/null; then
    echo "hermes-agent not found. Install it first:"
    echo "  pip install hermes-agent"
    echo "  # or: curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash"
    exit 1
fi

# ---------------------------------------------------------------------------
# 2. Ensure directories exist
# ---------------------------------------------------------------------------
mkdir -p "$HERMES_HOME/plugins"
mkdir -p "$HERMES_HOME/skills"

# ---------------------------------------------------------------------------
# 3. Symlink plugin
# ---------------------------------------------------------------------------
PLUGIN_LINK="$HERMES_HOME/plugins/forge-protocol"
if [ -L "$PLUGIN_LINK" ]; then
    echo "Removing old plugin symlink..."
    rm "$PLUGIN_LINK"
elif [ -d "$PLUGIN_LINK" ]; then
    echo "Removing old plugin directory..."
    rm -rf "$PLUGIN_LINK"
fi

ln -s "$SCRIPT_DIR/plugin" "$PLUGIN_LINK"
echo "Plugin linked:  $PLUGIN_LINK -> $SCRIPT_DIR/plugin"

# ---------------------------------------------------------------------------
# 4. Copy skills (symlinks break Python's rglob on 3.13+)
# ---------------------------------------------------------------------------
for skill_dir in "$SCRIPT_DIR/skills"/*/; do
    skill_name="$(basename "$skill_dir")"
    # Skip empty dirs
    [ -f "$skill_dir/SKILL.md" ] || continue

    skill_dest="$HERMES_HOME/skills/$skill_name"
    if [ -L "$skill_dest" ]; then
        rm "$skill_dest"
    fi
    if [ -d "$skill_dest" ]; then
        rm -rf "$skill_dest"
    fi

    cp -r "$skill_dir" "$skill_dest"
    echo "Skill copied:   $skill_dest"
done

# ---------------------------------------------------------------------------
# 5. Install/update SOUL.md
# ---------------------------------------------------------------------------
SOUL_FILE="$HERMES_HOME/SOUL.md"
ORCHESTRATOR_SOUL="$SCRIPT_DIR/souls/forge-orchestrator.md"

if [ -f "$SOUL_FILE" ]; then
    # Check if it's already the forge orchestrator
    if grep -q "Forge Protocol" "$SOUL_FILE" 2>/dev/null; then
        echo "SOUL.md already contains Forge Protocol — updating..."
        cp "$ORCHESTRATOR_SOUL" "$SOUL_FILE"
    else
        # Backup existing SOUL.md and append forge section
        BACKUP="$SOUL_FILE.backup.$(date +%Y%m%d%H%M%S)"
        cp "$SOUL_FILE" "$BACKUP"
        echo "Backed up existing SOUL.md to: $BACKUP"

        echo ""
        echo "Your existing SOUL.md has been backed up."
        echo "Choose an option:"
        echo "  1) Replace SOUL.md with Forge Orchestrator (recommended)"
        echo "  2) Append Forge Orchestrator to existing SOUL.md"
        echo "  3) Skip SOUL.md (use forge tools manually)"
        echo ""
        read -rp "Choice [1/2/3]: " choice

        case "$choice" in
            1)
                cp "$ORCHESTRATOR_SOUL" "$SOUL_FILE"
                echo "SOUL.md replaced with Forge Orchestrator."
                ;;
            2)
                echo "" >> "$SOUL_FILE"
                echo "---" >> "$SOUL_FILE"
                echo "" >> "$SOUL_FILE"
                cat "$ORCHESTRATOR_SOUL" >> "$SOUL_FILE"
                echo "Forge Orchestrator appended to SOUL.md."
                ;;
            3)
                echo "Skipped SOUL.md. You can manually set it later:"
                echo "  cp $ORCHESTRATOR_SOUL $SOUL_FILE"
                ;;
            *)
                echo "Invalid choice. Skipping SOUL.md."
                ;;
        esac
    fi
else
    cp "$ORCHESTRATOR_SOUL" "$SOUL_FILE"
    echo "SOUL.md created: $SOUL_FILE"
fi

# ---------------------------------------------------------------------------
# 6. Install Python dependencies for the plugin
# ---------------------------------------------------------------------------
echo ""
echo "Checking Python dependencies..."
if python3 -c "import yaml" 2>/dev/null; then
    echo "PyYAML: OK"
else
    echo "Installing PyYAML..."
    pip install pyyaml
fi

# ---------------------------------------------------------------------------
# Done
# ---------------------------------------------------------------------------
echo ""
echo "=== Forge Protocol installed! ==="
echo ""
echo "Start Hermes and try:"
echo "  /forge-mode    — Socratic thinking partner"
echo "  /anvil-mode    — Rigorous editor/critic"
echo "  /furnace-mode  — Idea stress-tester"
echo "  /executor-mode — Normal AI (no friction)"
echo "  /forge-status  — Check your cognitive sovereignty dashboard"
echo ""
echo "The orchestrator SOUL will automatically classify tasks and"
echo "warn you when you're delegating thinking work to the AI."
