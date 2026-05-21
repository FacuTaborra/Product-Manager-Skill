"""Register required Claude Code permissions in ~/.claude/settings.json."""

from __future__ import annotations

import json
import sys
from pathlib import Path


def _home_as_permission_path() -> str:
    """Return the home directory in the path format Claude Code permissions expect."""
    home = Path.home()
    if sys.platform == "win32":
        # C:\Users\name  →  //c/Users/name
        parts = home.parts
        drive = parts[0].rstrip(":\\").lower()
        rest = "/".join(parts[1:])
        return f"//{drive}/{rest}"
    return home.as_posix()


def _required_permissions() -> list[str]:
    home = _home_as_permission_path()
    return [
        "Bash(python3 ~/.claude/skills/pm/pm.py*)",
        f"Write({home}/.claude/tmp_*.md)",
    ]


def register_permissions() -> list[str]:
    """Merge PM skill permissions into ~/.claude/settings.json.

    Returns the list of entries that were actually added (empty if all already present).
    """
    settings_path = Path.home() / ".claude" / "settings.json"

    try:
        settings: dict = json.loads(settings_path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        settings = {}

    perms = settings.setdefault("permissions", {})
    allow: list[str] = perms.setdefault("allow", [])

    added: list[str] = []
    for entry in _required_permissions():
        if entry not in allow:
            allow.append(entry)
            added.append(entry)

    if added:
        settings_path.write_text(
            json.dumps(settings, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    return added
