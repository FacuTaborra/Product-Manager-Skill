"""Tests for SetupService using InMemoryCacheRepository and mock IssueProvider."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest

from src.claude_pm.application.setup_flow import SetupOptions, SetupService
from src.claude_pm.config import Config, PmFileConfig
from src.claude_pm.domain.models import Project, State, Team
from src.claude_pm.exceptions import NeedsChoice, PMError
from src.claude_pm.infrastructure.cache import Cache, InMemoryCacheRepository

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_config(repo_name: str = "my-repo", pm_file: PmFileConfig | None = None) -> Config:
    return Config(
        pak_file=MagicMock(),
        pak="test-key",
        vault_path=None,
        repo_name=repo_name,
        cache_path=MagicMock(),
        team_id_override=None,
        project_id_override=None,
        provider_name="linear",
        pm_file=pm_file or PmFileConfig(),
    )


_DEFAULT_TEAMS = [Team(id="team-1", name="My Team", key="MT")]
_DEFAULT_PROJECTS = [Project(id="proj-1", name="my-repo")]
_DEFAULT_STATES = [State(id="s1", name="Todo"), State(id="s2", name="Done")]


def _make_provider(
    teams: list[Team] | None = None,
    projects: list[Project] | None = None,
    states: list[State] | None = None,
) -> Any:
    provider = MagicMock()
    provider.list_teams.return_value = _DEFAULT_TEAMS if teams is None else teams
    provider.find_projects.return_value = _DEFAULT_PROJECTS if projects is None else projects
    provider.list_projects.return_value = _DEFAULT_PROJECTS if projects is None else projects
    provider.list_states.return_value = _DEFAULT_STATES if states is None else states
    return provider


def _fresh_cache() -> Cache:
    from datetime import datetime, timezone
    return Cache(
        team_id="team-1",
        project_id="proj-1",
        project_name="my-repo",
        projects=({"id": "proj-1", "name": "my-repo"},),
        state_ids={"Todo": "s1", "Done": "s2"},
        last_refresh=datetime.now(timezone.utc).isoformat(),
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestEnsureWithFreshCache:
    def test_fresh_complete_cache_skips_api(self) -> None:
        repo = InMemoryCacheRepository(initial=_fresh_cache())
        provider = _make_provider()
        service = SetupService(provider, repo, _make_config())

        cache = service.ensure()

        assert cache.team_id == "team-1"
        provider.list_teams.assert_not_called()
        provider.find_projects.assert_not_called()

    def test_force_true_re_runs_setup(self) -> None:
        repo = InMemoryCacheRepository(initial=_fresh_cache())
        provider = _make_provider()
        service = SetupService(provider, repo, _make_config())

        cache = service.ensure(SetupOptions(force=True))

        assert cache.team_id == "team-1"
        provider.list_teams.assert_called_once()


class TestEnsureWithEmptyCache:
    def test_single_team_auto_selected(self) -> None:
        repo = InMemoryCacheRepository()
        provider = _make_provider()
        service = SetupService(provider, repo, _make_config())

        cache = service.ensure()

        assert cache.team_id == "team-1"
        assert cache.project_id == "proj-1"
        assert cache.state_ids == {"Todo": "s1", "Done": "s2"}

    def test_multiple_teams_raises_needs_choice(self) -> None:
        repo = InMemoryCacheRepository()
        provider = _make_provider(teams=[
            Team(id="t1", name="Team A", key="A"),
            Team(id="t2", name="Team B", key="B"),
        ])
        service = SetupService(provider, repo, _make_config())

        with pytest.raises(NeedsChoice, match="Multiple teams found"):
            service.ensure()

    def test_team_id_override_is_used(self) -> None:
        repo = InMemoryCacheRepository()
        provider = _make_provider(teams=[
            Team(id="t1", name="Team A", key="A"),
            Team(id="t2", name="Team B", key="B"),
        ])
        service = SetupService(provider, repo, _make_config())

        cache = service.ensure(SetupOptions(team_id_override="t2"))

        assert cache.team_id == "t2"

    def test_unknown_team_override_raises(self) -> None:
        repo = InMemoryCacheRepository()
        provider = _make_provider()
        service = SetupService(provider, repo, _make_config())

        with pytest.raises(PMError, match="not found in this workspace"):
            service.ensure(SetupOptions(team_id_override="unknown-id"))

    def test_no_projects_raises_needs_choice(self) -> None:
        repo = InMemoryCacheRepository()
        provider = _make_provider(projects=[])
        service = SetupService(provider, repo, _make_config())

        with pytest.raises(NeedsChoice, match="No project matches"):
            service.ensure()

    def test_create_project_if_missing(self) -> None:
        repo = InMemoryCacheRepository()
        provider = _make_provider(projects=[])
        provider.create_project.return_value = Project(id="new-p", name="my-repo")
        service = SetupService(provider, repo, _make_config())

        cache = service.ensure(SetupOptions(create_project_if_missing=True))

        provider.create_project.assert_called_once_with("my-repo", "team-1")
        assert cache.project_id == "new-p"

    def test_multiple_matching_projects_raises(self) -> None:
        repo = InMemoryCacheRepository()
        provider = _make_provider(projects=[
            Project(id="p1", name="my-repo-v1"),
            Project(id="p2", name="my-repo-v2"),
        ])
        service = SetupService(provider, repo, _make_config())

        with pytest.raises(NeedsChoice, match="Multiple projects match"):
            service.ensure()

    def test_exact_name_match_preferred(self) -> None:
        repo = InMemoryCacheRepository()
        provider = _make_provider(projects=[
            Project(id="p1", name="my-repo-extra"),
            Project(id="p2", name="my-repo"),
        ])
        service = SetupService(provider, repo, _make_config())

        cache = service.ensure()
        assert cache.project_id == "p2"

    def test_written_cache_is_fresh_and_complete(self) -> None:
        repo = InMemoryCacheRepository()
        service = SetupService(_make_provider(), repo, _make_config())

        cache = service.ensure()

        assert cache.is_fresh()
        assert cache.is_complete()
