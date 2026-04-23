#!/usr/bin/env bash
# Forge Protocol installer for Hermes Agent.
#
# By default, copies plugin, lib, modes, and souls into a self-contained
# tree under $HERMES_HOME/plugins/forge-protocol/. Re-run after editing
# files in the repo to refresh the install.
#
# Use --dev to symlink the repo instead — useful when actively developing
# the plugin. With --dev, changes in the repo are visible to Hermes without
# re-running this script, but moving or deleting the repo breaks the install.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HERMES_HOME="${HERMES_HOME:-$HOME/.hermes}"
MODE="copy"

for arg in "$@"; do
    case "$arg" in
        --dev)  MODE="symlink" ;;
        -h|--help)
            echo "Usage: $0 [--dev]"
            echo "  (default)  copy the repo into \$HERMES_HOME/plugins/forge-protocol"
            echo "  --dev      symlink the repo for active development"
            exit 0
            ;;
    esac
done

echo "=== Forge Protocol Installer ==="
echo "Repo:        $SCRIPT_DIR"
echo "Hermes home: $HERMES_HOME"
echo "Install:     $MODE (use --dev to symlink)"
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

PLUGIN_ROOT="$HERMES_HOME/plugins/forge-protocol"

# ---------------------------------------------------------------------------
# 3. Install plugin (copy or symlink)
# ---------------------------------------------------------------------------
# Clean any previous install — may have been copy or symlink.
if [ -L "$PLUGIN_ROOT" ]; then
    rm "$PLUGIN_ROOT"
elif [ -d "$PLUGIN_ROOT" ]; then
    rm -rf "$PLUGIN_ROOT"
fi

if [ "$MODE" = "symlink" ]; then
    # Dev mode: a single symlink to the repo root. The plugin resolves
    # sibling dirs (lib, modes) relative to its own location, so pointing
    # the whole tree makes Python see the live repo.
    ln -s "$SCRIPT_DIR" "$PLUGIN_ROOT"
    echo "Plugin linked (dev):  $PLUGIN_ROOT -> $SCRIPT_DIR"
else
    # Prod mode: self-contained copy. Re-run install.sh after edits.
    mkdir -p "$PLUGIN_ROOT"
    cp -R "$SCRIPT_DIR/plugin/"*  "$PLUGIN_ROOT/"
    cp -R "$SCRIPT_DIR/lib"       "$PLUGIN_ROOT/lib"
    cp -R "$SCRIPT_DIR/modes"     "$PLUGIN_ROOT/modes"
    cp -R "$SCRIPT_DIR/souls"     "$PLUGIN_ROOT/souls"
    echo "Plugin copied:        $PLUGIN_ROOT"
fi

# ---------------------------------------------------------------------------
# 4. Copy skills (always copied — Python's rglob doesn't follow symlinks on 3.13+)
# ---------------------------------------------------------------------------
# Compute the current skill set from the repo.
CURRENT_SKILLS=()
for skill_dir in "$SCRIPT_DIR/skills"/*/; do
    [ -f "$skill_dir/SKILL.md" ] || continue
    CURRENT_SKILLS+=("$(basename "$skill_dir")")
done

# First pass: prune previously-installed Forge Protocol skills. We detect them
# by the `forge-protocol` tag in their SKILL.md frontmatter. Skills that are
# still in the current set get refreshed silently below; only *orphaned* skills
# (e.g. renamed or retired like the Furnace → Crucible rename) are announced.
if [ -d "$HERMES_HOME/skills" ]; then
    for existing_skill in "$HERMES_HOME/skills"/*/; do
        existing_skill_file="$existing_skill/SKILL.md"
        existing_skill_name="$(basename "$existing_skill")"
        [ -f "$existing_skill_file" ] || continue
        if grep -q "forge-protocol" "$existing_skill_file" 2>/dev/null; then
            rm -rf "$existing_skill"
            # Only log when this skill is truly orphaned (no longer in the repo).
            is_orphan=true
            for curr in "${CURRENT_SKILLS[@]}"; do
                [ "$curr" = "$existing_skill_name" ] && { is_orphan=false; break; }
            done
            if [ "$is_orphan" = true ]; then
                echo "Retired skill pruned: $existing_skill_name"
            fi
        fi
    done
fi

# Second pass: install the current skill set.
for skill_dir in "$SCRIPT_DIR/skills"/*/; do
    skill_name="$(basename "$skill_dir")"
    [ -f "$skill_dir/SKILL.md" ] || continue

    skill_dest="$HERMES_HOME/skills/$skill_name"
    if [ -L "$skill_dest" ]; then
        rm "$skill_dest"
    fi

    cp -r "$skill_dir" "$skill_dest"
    echo "Skill copied:         $skill_dest"
done

# Invalidate Hermes's skill snapshot cache so it re-scans on next launch.
# (Safe no-op if the cache doesn't exist yet.)
rm -f "$HERMES_HOME/.skills_prompt_snapshot.json"

# ---------------------------------------------------------------------------
# 5. Install/update SOUL.md
# ---------------------------------------------------------------------------
SOUL_FILE="$HERMES_HOME/SOUL.md"
ORCHESTRATOR_SOUL="$SCRIPT_DIR/souls/forge-orchestrator.md"

if [ -f "$SOUL_FILE" ]; then
    if grep -q "Forge Protocol" "$SOUL_FILE" 2>/dev/null; then
        # Re-install path: the user may have edited SOUL.md after the first
        # install. Skip the overwrite if the file already matches upstream;
        # otherwise back up before replacing, so local customizations are
        # never silently destroyed.
        if cmp -s "$ORCHESTRATOR_SOUL" "$SOUL_FILE"; then
            echo "SOUL.md already up to date."
        else
            BACKUP="$SOUL_FILE.backup.$(date +%Y%m%d%H%M%S)"
            cp "$SOUL_FILE" "$BACKUP"
            cp "$ORCHESTRATOR_SOUL" "$SOUL_FILE"
            echo "SOUL.md updated (previous version saved to $BACKUP)"
        fi
    else
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
    echo "SOUL.md created:      $SOUL_FILE"
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

echo ""
echo "Adversarial auditor (optional, recommended):"
echo "  A second Claude Sonnet instance independently judges compliance"
echo "  instead of having the primary model judge itself."
echo ""
echo "  Enable with:"
echo "    pip install anthropic            # or pip install 'forge-protocol[vertex]'"
echo "    export FORGE_AUDITOR_ENABLED=1"
echo ""

# ---------------------------------------------------------------------------
# Done
# ---------------------------------------------------------------------------
echo ""
echo "=== Forge Protocol installed! ==="
echo ""
echo "ONE MORE STEP — enable the plugin in Hermes:"
echo ""
echo "    hermes plugins enable forge-protocol"
echo ""
echo "Hermes ships all user-scope plugins as opt-in; without this command"
echo "the tools above will not load. Run it once and you're set."
echo ""
echo "Then start Hermes and try:"
echo "  /forge-mode     — Socratic thinking partner"
echo "  /anvil-mode     — Rigorous editor/critic"
echo "  /crucible-mode  — Idea stress-tester"
echo "  /executor-mode  — Normal AI (no friction)"
echo "  /forge-status   — Your cognitive-sovereignty dashboard"
echo "  /forge-audit    — Weekly canary for measurable skill tracking"
echo ""
echo "The orchestrator SOUL will classify tasks inline and warn you when"
echo "you're delegating thinking work to the AI."
