# claude-pm-skill

[![CI](https://github.com/FacuTaborra/product-manager-skill/actions/workflows/ci.yml/badge.svg)](https://github.com/FacuTaborra/product-manager-skill/actions/workflows/ci.yml)

A Claude Code skill that turns Claude into your project's **Project Manager**, backed by **Linear** or **ClickUp** (with an extensible provider architecture for GitHub Issues, Jira, etc.).

Two modes:

- **`/pm`** — Briefing of what's open, in progress, and blocked.
- **`/pm "task description"`** — Proposes a board of issues for the task, then creates them after your confirmation.

Designed to work in **any repo**, with or without an Obsidian vault for project context. Output (briefings, proposed boards, issue descriptions) is always written in the language you're using to talk to Claude.

---

## Requirements

- **Python 3.10+** (uses stdlib only at runtime — no `pip install` needed to use it)
- A **Linear** or **ClickUp** account with permission to create issues
- **Claude Code** CLI installed ([install guide](https://docs.anthropic.com/claude/docs/claude-code))

---

## Install

### Linux / macOS / Git Bash on Windows

```bash
git clone https://github.com/FacuTaborra/product-manager-skill.git
cd claude-pm-skill
./install.sh
```

### Windows (native PowerShell)

```powershell
git clone https://github.com/FacuTaborra/product-manager-skill.git
cd claude-pm-skill
.\install.ps1
```

The installer copies `SKILL.md` and `pm.py` to `~/.claude/skills/pm/` and creates the secrets directory if it doesn't exist.

### Optional: add the `pm` shell alias

To run `pm doctor` instead of the full `python3 ~/.claude/skills/pm/pm.py doctor`:

**Git Bash / Linux / macOS** — add to `~/.bashrc` or `~/.zshrc`:
```bash
alias pm='python3 ~/.claude/skills/pm/pm.py'
```

**PowerShell** — add to your `$PROFILE`:
```powershell
function pm { python3 "$HOME/.claude/skills/pm/pm.py" @args }
```

---

## Providers

The skill supports two issue trackers out of the box. Pick one per project.

| Provider | Issue format | Notes |
|----------|-------------|-------|
| **Linear** (default) | Teams → Projects → Issues | GraphQL API. Best for eng-focused teams. |
| **ClickUp** | Spaces → Lists → Tasks | REST API. Also supports Docs (create/update). |

The active provider is resolved in this order:
1. `PM_PROVIDER` environment variable
2. `projects.pm` file in the skill directory (per-repo config)
3. Default: `linear`

---

## Configure: Linear

1. Go to <https://linear.app/settings/api>
2. Click **Create new API key**
3. Name it (e.g. `claude-pm-skill`), grant **Read + Write** scopes
4. Copy the key (starts with `lin_api_...`)
5. Create `~/.claude/secrets/linear-pak.env`:
   ```
   LINEAR_API_KEY=lin_api_xxxxxxxxxxxxxxx
   ```
6. Lock down the file (Linux/macOS):
   ```bash
   chmod 600 ~/.claude/secrets/linear-pak.env
   ```

Verify:

```bash
pm doctor
```

You should see `Linear ping: ok — authenticated as <your email>`.

---

## Configure: ClickUp

1. Go to **ClickUp → Settings → Apps** (or <https://app.clickup.com/settings/apps>)
2. Under **API Token**, click **Generate** (or copy if already generated)
3. The token starts with `pk_`
4. Create `~/.claude/secrets/clickup-pak.env`:
   ```
   CLICKUP_API_KEY=pk_xxxxxxxxxxxxxxx
   ```
5. Lock down the file (Linux/macOS):
   ```bash
   chmod 600 ~/.claude/secrets/clickup-pak.env
   ```
6. Tell the skill to use ClickUp. Either:
   - Set in your shell: `export PM_PROVIDER=clickup`
   - Or configure per-repo in `projects.pm` (see [Per-repo config](#per-repo-config) below)

Verify:

```bash
PM_PROVIDER=clickup pm doctor
```

You should see `ClickUp ping: ok — authenticated as <your email>`.

### ClickUp hierarchy mapping

ClickUp's structure maps to the skill's concepts like this:

| ClickUp | Skill concept |
|---------|--------------|
| Workspace | (auto-detected, one per account) |
| Space | Team |
| List | Project |
| Task | Issue |
| Status | State |

---

## Per-repo config

For projects where the provider or IDs differ from your defaults, create a `projects.pm` file in the skill directory (`~/.claude/skills/pm/projects.pm`). Each section is a repo name:

```ini
# Linear project (default provider, no section needed unless you want explicit IDs)
[my-linear-repo]
provider: linear
space: lin_team_xxxxxxxxxx
project: lin_project_xxxxxxxxxx

# ClickUp project
[my-clickup-repo]
provider: clickup
space: 12345678          # Space ID
project: 87654321        # List ID
```

The `space` and `project` keys are optional — if omitted, the skill auto-discovers them from the API (same as with env var overrides).

---

## Usage

Open Claude Code in any project, then:

```
/pm
```

→ briefing of open issues for the current repo.

```
/pm let's add a multi-tenant billing feature
```

→ Claude proposes a board of issues, asks for your confirmation, and creates them in your issue tracker.

The skill auto-detects the **project name** from the current directory (or `.claude-session-name` if present) and looks up the matching project. On first use it caches the team/project IDs so subsequent calls are fast.

---

## Environment variables

All optional — the defaults work for most setups.

### Linear

| Variable | Default | What it does |
|---|---|---|
| `LINEAR_PAK_FILE` | `~/.claude/secrets/linear-pak.env` | Where the Linear PAK lives. |
| `LINEAR_TEAM_ID` | (none) | Override auto-detected team. |
| `LINEAR_PROJECT_ID` | (none) | Override auto-detected project. Useful if the Linear project name differs from the repo name. |

### ClickUp

| Variable | Default | What it does |
|---|---|---|
| `CLICKUP_PAK_FILE` | `~/.claude/secrets/clickup-pak.env` | Where the ClickUp token lives. |
| `CLICKUP_SPACE_ID` | (none) | Override auto-detected Space (equivalent to team). |
| `CLICKUP_LIST_ID` | (none) | Override auto-detected List (equivalent to project). |

### General

| Variable | Default | What it does |
|---|---|---|
| `PM_PROVIDER` | `linear` | Active provider: `linear` or `clickup`. |
| `CLAUDE_MEMORY_PATH` | `~/.claude-memory` | Path to an Obsidian vault. If it exists, the skill reads `proyectos/<repo>/STATUS.md` to enrich briefings. |

---

## Team setup

An issue tracker **team/space** is a shared board — multiple developers can use this skill against the same project. Issues you create show up for the whole team in real time. Each developer uses their own Personal API Key.

### First developer (creates the project)

```bash
git clone <repo>
cd <repo>
./install.sh    # or .\install.ps1 on Windows
```

Edit `~/.claude/secrets/linear-pak.env` (or `clickup-pak.env`) with your PAK, then in Claude:

```
/pm
```

If no project matches the repo name, the skill tells you. Either:

- Re-run setup to create one:
  ```bash
  pm setup --create-project
  ```
- Or point the skill at an existing project:
  ```bash
  pm setup --project-id <project-id>
  ```

### Other developers on the team

Same install, but the skill finds the existing project automatically:

```bash
git clone <repo>
cd <repo>
./install.sh
# edit ~/.claude/secrets/linear-pak.env (or clickup-pak.env) with YOUR own PAK
```

Then `/pm` from Claude — no manual setup needed.

### Project name doesn't match the repo

**Linear** — set `LINEAR_PROJECT_ID` in your shell profile:

```bash
export LINEAR_PROJECT_ID=<uuid-of-the-linear-project>
```

**ClickUp** — set `CLICKUP_LIST_ID`:

```bash
export PM_PROVIDER=clickup
export CLICKUP_LIST_ID=<clickup-list-id>
```

Or configure both in `projects.pm` (see [Per-repo config](#per-repo-config)).

### Assigning issues to teammates

Tell Claude: *"propose this task and assign it to juan@team.com"*. The skill resolves the email to a user ID via `pm resolve-user` and passes `--assignee` to `create-issue`. The teammate must already exist in your workspace.

### Using your team's labels

If your team uses labels (`feature`, `bug`, `tech-debt`, etc.), tell Claude: *"…with the `feature` and `backend` labels"*. Labels must **already exist** in the team — the skill won't auto-create them (avoids typos becoming new labels). Run `pm list-labels` to see what's available.

> **ClickUp note:** ClickUp's v2 API doesn't expose labels (tags). Use statuses and priorities instead.

### Security

- **PAKs are personal — never commit `linear-pak.env` or `clickup-pak.env`.** Each developer generates their own.
- Each developer's `~/.claude/secrets/` is local. No shared secrets.

---

## Optional: Obsidian vault integration

If you keep project notes in an Obsidian vault following this layout:

```
<vault>/
└── proyectos/
    └── <repo-name>/
        ├── STATUS.md       # what's in flight, last sessions, blockers
        └── .linear-cache.json   # or .clickup-cache.json
```

…then the skill reads `STATUS.md` and includes a 1–2 line summary in the briefing. Set `CLAUDE_MEMORY_PATH` to your vault root.

The skill works fine without a vault — briefings just rely on tracker data only.

---

## Troubleshooting

### `Linear API key not found` / `ClickUp API key not found`

The PAK file is missing or has a malformed line. Run `pm doctor` to see where it's looking, then check that the file exists and contains the correct key.

- Linear: `LINEAR_API_KEY=lin_api_...` in `~/.claude/secrets/linear-pak.env`
- ClickUp: `CLICKUP_API_KEY=pk_...` in `~/.claude/secrets/clickup-pak.env`

### `Multiple teams found. Pick one and re-run with --team-id`

Your workspace has more than one team/space. Run `pm list-teams` to see them, then:

```bash
pm setup --team-id <id>
```

Or set `LINEAR_TEAM_ID` / `CLICKUP_SPACE_ID` in your shell profile.

### `No project matches '<repo>' in this team`

The project/list doesn't exist. Either create it (`setup --create-project`) or use an existing one with a different name (`setup --project-id <id>`).

### `Label 'X' not found in this team`

Run `pm list-labels` to see what exists. Either pick one of those, or create the label in your tracker's UI first (the skill won't auto-create labels).

> ClickUp: `list-labels` returns empty because the ClickUp v2 API doesn't expose tags. Use statuses instead.

### `No member with email 'X' in this workspace`

Check that the email matches the one your tracker has for that user. Use `pm resolve-user <email>` to verify.

### Cache seems stale

```bash
pm setup --force
```

This re-discovers team, project, and state IDs from your issue tracker.

### Switching providers mid-project

Change `PM_PROVIDER` (or update `projects.pm`) and run:

```bash
pm setup --force
```

This discards the old cache and builds a fresh one for the new provider.

---

## How it's wired

The skill follows a **hexagonal (ports & adapters)** architecture so that any issue tracker can be plugged in without touching the rest of the code.

```
src/claude_pm/
├── domain/           # Issue, Team, Project, ... (frozen dataclasses)
│                     # IssueProvider, ContextProvider (typing.Protocol)
├── infrastructure/   # LinearProvider, ClickUpProvider, ObsidianVaultContext,
│                     # HttpClient, Cache, ProviderRegistry
├── application/      # BriefingService, SetupService, SearchService, CreateIssueService
└── commands/         # CLI handlers — wire argparse to services
```

- **`SKILL.md`** — what Claude reads. Tells Claude how to detect mode, present briefings, propose boards, and call the CLI.
- **`pm.py`** (root) — a thin wrapper that delegates to the `claude_pm` package.
- **Provider selection** — `_registry.py` maps provider name → class at runtime. Adding a new tracker means implementing `IssueProvider` and registering it there.
- **Cache** — `<vault>/proyectos/<repo>/.linear-cache.json` (or `.clickup-cache.json`) if a vault is configured, else `~/.config/claude-pm-skill/<repo>/`.

The CLI handles API plumbing (HTTP, JSON, retries, error parsing); Claude handles the conversation.

To add a new tracker (GitHub, Jira, …), implement the `IssueProvider` Protocol — see [CONTRIBUTING.md](./CONTRIBUTING.md).

---

## Contributing

Issues and PRs welcome. See [CONTRIBUTING.md](./CONTRIBUTING.md) for the project layout, how to add a new provider, and local dev setup (`ruff`, `mypy`, smoke tests).

---

## License

MIT — see [LICENSE](./LICENSE).
