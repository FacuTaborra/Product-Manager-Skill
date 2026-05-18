"""Tests for Cache (frozen dataclass) and CacheRepository implementations."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from src.claude_pm.infrastructure.cache import (
    Cache,
    InMemoryCacheRepository,
    JsonFileCacheRepository,
)


class TestCacheIsFresh:
    def test_fresh_when_recent(self) -> None:
        ts = datetime.now(timezone.utc).isoformat()
        cache = Cache(team_id="t1", last_refresh=ts)
        assert cache.is_fresh()

    def test_stale_when_old(self) -> None:
        ts = (datetime.now(timezone.utc) - timedelta(days=31)).isoformat()
        cache = Cache(team_id="t1", last_refresh=ts)
        assert not cache.is_fresh()

    def test_not_fresh_when_no_refresh(self) -> None:
        cache = Cache(team_id="t1")
        assert not cache.is_fresh()

    def test_not_fresh_on_malformed_ts(self) -> None:
        cache = Cache(team_id="t1", last_refresh="not-a-date")
        assert not cache.is_fresh()


class TestCacheIsComplete:
    def test_complete_when_all_present(self) -> None:
        cache = Cache(
            team_id="t1",
            projects=({"id": "p1", "name": "proj"},),
            state_ids={"Todo": "s1"},
        )
        assert cache.is_complete()

    def test_incomplete_when_missing_team(self) -> None:
        cache = Cache(projects=({"id": "p1", "name": "proj"},), state_ids={"Todo": "s1"})
        assert not cache.is_complete()

    def test_incomplete_when_no_projects(self) -> None:
        cache = Cache(team_id="t1", state_ids={"Todo": "s1"})
        assert not cache.is_complete()

    def test_incomplete_when_no_states(self) -> None:
        cache = Cache(team_id="t1", projects=({"id": "p1", "name": "proj"},))
        assert not cache.is_complete()


class TestJsonFileCacheRepository:
    def test_load_missing_file_returns_empty_cache(self, tmp_path: Path) -> None:
        repo = JsonFileCacheRepository(tmp_path / "cache.json")
        cache = repo.load()
        assert cache == Cache()

    def test_load_corrupted_file_returns_empty_cache(self, tmp_path: Path) -> None:
        path = tmp_path / "cache.json"
        path.write_text("this is not json", encoding="utf-8")
        repo = JsonFileCacheRepository(path)
        cache = repo.load()
        assert cache == Cache()

    def test_write_persists_to_disk(self, tmp_path: Path) -> None:
        repo = JsonFileCacheRepository(tmp_path / "cache.json")
        cache = repo.write(
            team_id="team-1",
            project_id="proj-1",
            project_name="My Project",
            state_ids={"Todo": "state-1", "Done": "state-2"},
        )
        assert cache.team_id == "team-1"
        assert cache.project_id == "proj-1"
        assert cache.project_name == "My Project"
        assert cache.state_ids == {"Todo": "state-1", "Done": "state-2"}
        assert (tmp_path / "cache.json").is_file()

    def test_write_then_load_round_trips(self, tmp_path: Path) -> None:
        repo = JsonFileCacheRepository(tmp_path / "cache.json")
        repo.write(
            team_id="team-1",
            project_id="proj-1",
            project_name="My Project",
            state_ids={"Todo": "state-1"},
        )
        loaded = repo.load()
        assert loaded.team_id == "team-1"
        assert loaded.project_id == "proj-1"
        assert loaded.state_ids == {"Todo": "state-1"}

    def test_write_multi_persists_projects(self, tmp_path: Path) -> None:
        repo = JsonFileCacheRepository(tmp_path / "cache.json")
        projects = [{"id": "p1", "name": "Proj A"}, {"id": "p2", "name": "Proj B"}]
        cache = repo.write_multi(
            team_id="team-1",
            projects=projects,
            state_ids={"Todo": "s1"},
        )
        assert len(cache.projects) == 2
        assert cache.projects[0] == {"id": "p1", "name": "Proj A"}

    def test_load_backward_compat_single_project(self, tmp_path: Path) -> None:
        path = tmp_path / "cache.json"
        path.write_text(
            json.dumps({
                "linearTeamId": "t1",
                "linearProjectId": "p1",
                "linearProjectName": "Proj",
                "stateIds": {"Todo": "s1"},
                "lastRefresh": datetime.now(timezone.utc).isoformat(),
            }),
            encoding="utf-8",
        )
        repo = JsonFileCacheRepository(path)
        cache = repo.load()
        assert len(cache.projects) == 1
        assert cache.projects[0] == {"id": "p1", "name": "Proj"}

    def test_creates_parent_dirs(self, tmp_path: Path) -> None:
        nested = tmp_path / "deep" / "nested" / "cache.json"
        repo = JsonFileCacheRepository(nested)
        repo.write(team_id="t1", project_id="p1", project_name="P", state_ids={})
        assert nested.is_file()


class TestInMemoryCacheRepository:
    def test_load_returns_empty_by_default(self) -> None:
        repo = InMemoryCacheRepository()
        assert repo.load() == Cache()

    def test_load_returns_initial_cache(self) -> None:
        initial = Cache(team_id="t1")
        repo = InMemoryCacheRepository(initial=initial)
        assert repo.load().team_id == "t1"

    def test_write_updates_state(self) -> None:
        repo = InMemoryCacheRepository()
        repo.write(team_id="t1", project_id="p1", project_name="P", state_ids={"Todo": "s1"})
        cache = repo.load()
        assert cache.team_id == "t1"
        assert cache.state_ids == {"Todo": "s1"}

    def test_write_multi_updates_state(self) -> None:
        repo = InMemoryCacheRepository()
        repo.write_multi(
            team_id="t1",
            projects=[{"id": "p1", "name": "Proj A"}],
            state_ids={"Done": "s2"},
        )
        cache = repo.load()
        assert len(cache.projects) == 1
        assert cache.state_ids == {"Done": "s2"}

    def test_is_fresh_after_write(self) -> None:
        repo = InMemoryCacheRepository()
        repo.write(team_id="t1", project_id="p1", project_name="P", state_ids={"Todo": "s1"})
        assert repo.load().is_fresh()
