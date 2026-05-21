# claude-pm-skill

[![CI](https://github.com/FacuTaborra/product-manager-skill/actions/workflows/ci.yml/badge.svg)](https://github.com/FacuTaborra/product-manager-skill/actions/workflows/ci.yml)

Un skill para Claude Code que convierte a Claude en tu Project Manager, conectado a **Linear** o **ClickUp**.

En vez de abrir el tracker, revisar qué hay abierto, pensar qué issues crear y completar formularios — le describís la tarea a Claude y él se encarga. Sabe qué está en progreso, qué está bloqueado, y puede proponer un board completo de issues (con títulos, descripciones y prioridades) antes de crear cualquier cosa.

```
/pm                          → resumen de lo que está abierto, en progreso y bloqueado
/pm "agregar multi-tenant"   → propone un board de issues y los crea al confirmar
```

Funciona en **cualquier repo** y responde siempre en el idioma que usás para hablar con Claude.

---

## Requisitos

- Python 3.10+ (solo stdlib, sin `pip install`)
- Cuenta en Linear o ClickUp con permisos para crear issues
- [Claude Code](https://docs.anthropic.com/claude/docs/claude-code) instalado

---

## Instalación

**Linux / macOS / Git Bash:**
```bash
git clone https://github.com/FacuTaborra/product-manager-skill.git
cd claude-pm-skill
./install.sh
```

**Windows (PowerShell):**
```powershell
git clone https://github.com/FacuTaborra/product-manager-skill.git
cd claude-pm-skill
.\install.ps1
```

### Alias `pm` (opcional pero recomendado)

**Bash / Zsh** — agregar a `~/.bashrc` o `~/.zshrc`:
```bash
alias pm='python3 ~/.claude/skills/pm/pm.py'
```

**PowerShell** — agregar a `$PROFILE`:
```powershell
function pm { python3 "$HOME/.claude/skills/pm/pm.py" @args }
```

### Permisos de Claude Code

Los scripts de instalación registran automáticamente los permisos necesarios en `~/.claude/settings.json` para que Claude Code nunca pida confirmación al invocar el skill:

- `Bash(python3 ~/.claude/skills/pm/pm.py*)` — ejecutar el CLI
- `Write(~/.claude/tmp_*.md)` — archivos temporales para descripciones largas

Si actualizás el skill, `pm setup --force` también actualiza los permisos.

---

## Configuración

### Linear

1. Ir a <https://linear.app/settings/api> → **Create new API key** (permisos Read + Write)
2. La key empieza con `lin_api_...`
3. Crear el archivo `.env` en la raíz del repo (o en `~/.claude/secrets/linear-pak.env` para que aplique globalmente):
   ```
   LINEAR_API_KEY=lin_api_xxxxxxxxxxxxxxx
   ```
4. Verificar:
   ```bash
   pm doctor
   ```
   Tenés que ver `Linear ping: ok — authenticated as <tu email>`.

### ClickUp

1. Ir a **ClickUp → Settings → Apps** → copiar el API Token (empieza con `pk_`)
2. Crear el archivo `.env` en la raíz del repo (o en `~/.claude/secrets/clickup-pak.env` globalmente):
   ```
   CLICKUP_API_KEY=pk_xxxxxxxxxxxxxxx
   PM_PROVIDER=clickup
   ```
3. Verificar:
   ```bash
   pm doctor
   ```
   Tenés que ver `ClickUp ping: ok — authenticated as <tu email>`.

> **Nota:** El archivo `.env` local tiene prioridad sobre el global. Podés tener una key distinta por repo.

---

## Configuración por repo (`projects.pm`)

Si trabajás con varios repos y cada uno usa un provider o proyecto distinto, podés centralizarlo en `~/.claude/skills/pm/projects.pm`. Cada sección es el nombre del repo (el mismo nombre que el directorio):

```ini
[mi-repo-linear]
provider: linear
space: lin_team_xxxxxxxxxx    # opcional — si no está, lo auto-detecta
project: lin_project_xxxxxxx  # opcional

[mi-repo-clickup]
provider: clickup
space: 12345678               # Space ID — opcional
project: 87654321             # List ID — opcional
```

Si no existe `projects.pm`, el skill usa el provider del `.env` del repo actual (o `linear` por defecto) y auto-detecta el equipo y proyecto por nombre.

---

## Uso

Abrí Claude Code en cualquier proyecto y usá `/pm`:

```
/pm
```
→ briefing de issues abiertos del repo actual.

```
/pm agreguemos un sistema de notificaciones por email
```
→ Claude propone un board de issues, pedís confirmación, y los crea en tu tracker.

El skill detecta el nombre del proyecto desde el directorio actual y busca el proyecto correspondiente. La primera vez cachea los IDs del equipo/proyecto; las siguientes llamadas son rápidas.

---

## Comandos útiles

### Setup y diagnóstico

```bash
pm doctor                          # verifica configuración y conectividad
pm setup                           # descubre y cachea team/proyecto/estados
pm setup --force                   # fuerza re-discovery (útil si algo cambió)
pm setup --create-project          # crea el proyecto si no existe en el tracker
pm setup --project-id <id>         # apunta a un proyecto existente con otro nombre
```

### Issues

```bash
pm briefing                        # resumen de issues del proyecto actual
pm get-issue --id <id>             # obtiene un issue con su descripción completa
pm create-issue --title "..." --state todo --priority 2
pm update-issue --id <id> --state complete
pm update-issue --id <id> --title "nuevo título" --priority 1
pm search "query"                  # busca issues (útil para detectar duplicados)
```

### Lookups

```bash
pm list-teams                      # lista equipos/spaces disponibles
pm list-projects                   # lista proyectos del equipo
pm list-states                     # lista estados disponibles (todo, in-progress, etc.)
pm list-labels                     # lista etiquetas del equipo
pm resolve-user email@example.com  # obtiene el ID de un usuario por email
```
