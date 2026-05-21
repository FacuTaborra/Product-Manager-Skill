#Requires -Version 5.1
# claude-pm-skill installer (Windows PowerShell).
# Creates a junction ~/.claude/skills/pm/ -> repo root and seeds the secret file.

$ErrorActionPreference = "Stop"

$RepoRoot   = Split-Path -Parent $MyInvocation.MyCommand.Path
$ClaudeDir  = if ($env:CLAUDE_DIR) { $env:CLAUDE_DIR } else { Join-Path $HOME ".claude" }
$SkillDir   = Join-Path $ClaudeDir "skills\pm"
$SecretsDir = Join-Path $ClaudeDir "secrets"
$SecretFile = Join-Path $SecretsDir "linear-pak.env"
$ExampleFile = Join-Path $RepoRoot "examples\linear-pak.env.example"

Write-Host "claude-pm-skill installer"
Write-Host "  repo:    $RepoRoot"
Write-Host "  target:  $SkillDir"

if (-not (Test-Path $ClaudeDir)) {
    Write-Host ""
    Write-Host "WARN: $ClaudeDir does not exist." -ForegroundColor Yellow
    Write-Host "      Install Claude Code first: https://docs.anthropic.com/claude/docs/claude-code"
    Write-Host "      Continuing anyway - directories will be created."
}

# Create junction: skills\pm\ -> repo root (junction doesn't need admin/Dev Mode)
if (Test-Path $SkillDir) { Remove-Item -Path $SkillDir -Recurse -Force }
New-Item -ItemType Directory -Path (Split-Path $SkillDir) -Force | Out-Null
New-Item -ItemType Junction -Path $SkillDir -Target $RepoRoot | Out-Null
Write-Host "  -> $SkillDir -> $RepoRoot (junction)"

New-Item -ItemType Directory -Path $SecretsDir -Force | Out-Null

if (Test-Path $SecretFile) {
    Write-Host "  = $SecretFile (kept existing)"
} else {
    Copy-Item -Path $ExampleFile -Destination $SecretFile -Force
    Write-Host "  + $SecretFile (template - edit it to add your real key)"
}

# Register required Claude Code permissions via the skill's own module
$pythonScript = @"
import sys
sys.path.insert(0, r"$SkillDir\src")
from claude_pm.application.permissions import register_permissions

added = register_permissions()
for p in added:
    print(f'  + added permission: {p}')
if not added:
    print('  = all permissions already present')
"@

$pythonScript | python3 -

Write-Host ""
Write-Host "Installed."
Write-Host ""
Write-Host "Next steps:"
Write-Host "  1. Edit $SecretFile and replace REPLACE_ME with your Linear PAK."
Write-Host "     Get one at https://linear.app/settings/api (scope: read + write)."
Write-Host "  2. Verify with: python $SkillDir\pm.py doctor"
Write-Host "  3. Open Claude Code in any project and run: /pm"
