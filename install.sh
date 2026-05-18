#!/usr/bin/env bash
# claude-pm-skill installer (Linux / macOS / Git Bash on Windows).
# Creates a symlink ~/.claude/skills/pm/ -> repo root and seeds the secret file.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")" && pwd)"
CLAUDE_DIR="${CLAUDE_DIR:-$HOME/.claude}"
SKILL_DIR="$CLAUDE_DIR/skills/pm"
SECRETS_DIR="$CLAUDE_DIR/secrets"
SECRET_FILE="$SECRETS_DIR/linear-pak.env"
EXAMPLE_FILE="$REPO_ROOT/examples/linear-pak.env.example"

echo "claude-pm-skill installer"
echo "  repo:       $REPO_ROOT"
echo "  target:     $SKILL_DIR"

if [ ! -d "$CLAUDE_DIR" ]; then
  echo
  echo "WARN: $CLAUDE_DIR does not exist."
  echo "      Install Claude Code first: https://docs.anthropic.com/claude/docs/claude-code"
  echo "      Continuing anyway — directories will be created."
fi

# Create symlink: skills/pm/ -> repo root (rm handles both dir and existing symlink)
rm -rf "$SKILL_DIR"
mkdir -p "$(dirname "$SKILL_DIR")"
ln -s "$REPO_ROOT" "$SKILL_DIR"
echo "  → $SKILL_DIR -> $REPO_ROOT (symlink)"

mkdir -p "$SECRETS_DIR"
chmod 700 "$SECRETS_DIR" 2>/dev/null || true

if [ -f "$SECRET_FILE" ]; then
  echo "  = $SECRET_FILE (kept existing)"
else
  cp "$EXAMPLE_FILE" "$SECRET_FILE"
  chmod 600 "$SECRET_FILE" 2>/dev/null || true
  echo "  + $SECRET_FILE (template — edit it to add your real key)"
fi


# Add pm.py permission to ~/.claude/settings.json so Claude never prompts for it
SETTINGS_FILE="$CLAUDE_DIR/settings.json"
PM_PERMISSION="Bash(python3 ~/.claude/skills/pm/pm.py *)"

python3 - <<PYEOF
import json, os, sys

settings_file = "$SETTINGS_FILE"
permission = "$PM_PERMISSION"

if not os.path.exists(settings_file):
    data = {}
else:
    with open(settings_file) as f:
        data = json.load(f)

data.setdefault("permissions", {}).setdefault("allow", [])
if permission not in data["permissions"]["allow"]:
    data["permissions"]["allow"].append(permission)
    with open(settings_file, "w") as f:
        json.dump(data, f, indent=2)
    print(f"  + added permission: {permission}")
else:
    print(f"  = permission already present: {permission}")
PYEOF

echo
echo "Installed."
echo
echo "Next steps:"
echo "  1. Edit $SECRET_FILE and replace REPLACE_ME with your Linear PAK."
echo "     Get one at https://linear.app/settings/api (scope: read + write)."
echo "  2. Verify with: python3 $SKILL_DIR/pm.py doctor"
echo "  3. Open Claude Code in any project and run: /pm"
