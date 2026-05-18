"""Local JSON cache for the team/project/state IDs discovered during setup."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol

CACHE_TTL_DAYS = 30


@dataclass(frozen=True)
class Cache:
    """Immutable snapshot of cached provider IDs."""

    team_id: str | None = None
    project_id: str | None = None
    project_name: str | None = None
    projects: tuple[dict[str, str], ...] = field(default_factory=tuple)
    state_ids: dict[str, str] = field(default_factory=dict)
    last_refresh: str | None = None

    def is_fresh(self) -> bool:
        if not self.last_refresh:
            return False
        try:
            last = datetime.fromisoformat(self.last_refresh.replace("Z", "+00:00"))
        except ValueError:
            return False
        age = datetime.now(timezone.utc) - last
        return age.days < CACHE_TTL_DAYS

    def is_complete(self) -> bool:
        return bool(self.team_id and self.projects and self.state_ids)


class CacheRepository(Protocol):
    def load(self) -> Cache: ...

    def write(
        self,
        *,
        team_id: str,
        project_id: str,
        project_name: str,
        state_ids: dict[str, str],
    ) -> Cache: ...

    def write_multi(
        self,
        *,
        team_id: str,
        projects: list[dict[str, str]],
        state_ids: dict[str, str],
    ) -> Cache: ...


class JsonFileCacheRepository:
    def __init__(self, path: Path) -> None:
        self.path = path

    def load(self) -> Cache:
        if self.path.is_file():
            try:
                data: dict[str, Any] = json.loads(self.path.read_text(encoding="utf-8"))
                return _cache_from_dict(data)
            except (OSError, json.JSONDecodeError):
                pass
        return Cache()

    def write(
        self,
        *,
        team_id: str,
        project_id: str,
        project_name: str,
        state_ids: dict[str, str],
    ) -> Cache:
        data: dict[str, Any] = {
            "linearTeamId": team_id,
            "linearProjectId": project_id,
            "linearProjectName": project_name,
            "stateIds": state_ids,
            "lastRefresh": datetime.now(timezone.utc).isoformat(),
        }
        self._save(data)
        return _cache_from_dict(data)

    def write_multi(
        self,
        *,
        team_id: str,
        projects: list[dict[str, str]],
        state_ids: dict[str, str],
    ) -> Cache:
        first = projects[0] if projects else {}
        data: dict[str, Any] = {
            "linearTeamId": team_id,
            "linearProjectId": first.get("id"),
            "linearProjectName": first.get("name"),
            "projects": projects,
            "stateIds": state_ids,
            "lastRefresh": datetime.now(timezone.utc).isoformat(),
        }
        self._save(data)
        return _cache_from_dict(data)

    def _save(self, data: dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


class InMemoryCacheRepository:
    """In-memory implementation for tests — no filesystem I/O."""

    def __init__(self, initial: Cache | None = None) -> None:
        self._cache = initial or Cache()

    def load(self) -> Cache:
        return self._cache

    def write(
        self,
        *,
        team_id: str,
        project_id: str,
        project_name: str,
        state_ids: dict[str, str],
    ) -> Cache:
        self._cache = Cache(
            team_id=team_id,
            project_id=project_id,
            project_name=project_name,
            projects=({"id": project_id, "name": project_name},),
            state_ids=state_ids,
            last_refresh=datetime.now(timezone.utc).isoformat(),
        )
        return self._cache

    def write_multi(
        self,
        *,
        team_id: str,
        projects: list[dict[str, str]],
        state_ids: dict[str, str],
    ) -> Cache:
        first = projects[0] if projects else {}
        self._cache = Cache(
            team_id=team_id,
            project_id=first.get("id"),
            project_name=first.get("name"),
            projects=tuple(projects),
            state_ids=state_ids,
            last_refresh=datetime.now(timezone.utc).isoformat(),
        )
        return self._cache


def _cache_from_dict(data: dict[str, Any]) -> Cache:
    team_id_raw = data.get("linearTeamId")
    project_id_raw = data.get("linearProjectId")
    project_name_raw = data.get("linearProjectName")
    team_id = str(team_id_raw) if team_id_raw else None
    project_id = str(project_id_raw) if project_id_raw else None
    project_name = str(project_name_raw) if project_name_raw else None

    raw_projects = data.get("projects", [])
    if raw_projects:
        projects: tuple[dict[str, str], ...] = tuple(
            {"id": str(p["id"]), "name": str(p["name"])} for p in raw_projects
        )
    elif project_id and project_name:
        # backward compat: wrap single project
        projects = ({"id": project_id, "name": project_name},)
    else:
        projects = ()

    raw_states = data.get("stateIds", {})
    state_ids = (
        {str(k): str(v) for k, v in raw_states.items()} if isinstance(raw_states, dict) else {}
    )

    return Cache(
        team_id=team_id,
        project_id=project_id,
        project_name=project_name,
        projects=projects,
        state_ids=state_ids,
        last_refresh=data.get("lastRefresh"),
    )
