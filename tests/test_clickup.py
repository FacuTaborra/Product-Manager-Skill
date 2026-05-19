"""Regression tests for ClickUpProvider — covers the 3 adapter bugs:

1. search query not URL-encoded (crashed on spaces)
2. resolve_user_by_email hitting a non-existent endpoint (404)
3. list_states returning the internal status id instead of the name (400 on create)
"""

from __future__ import annotations

from typing import Any

from src.claude_pm.infrastructure.providers.clickup import ClickUpProvider


class FakeHttp:
    """Minimal HttpClient stand-in. Records GET URLs, replays canned JSON."""

    def __init__(self, responses: dict[str, Any]) -> None:
        self.headers = {"Authorization": "test-key"}
        self._responses = responses
        self.get_urls: list[str] = []

    def get_json(self, url: str) -> Any:
        self.get_urls.append(url)
        # Match on the path (query string ignored) using the most specific
        # (longest) registered key that it starts with.
        path = url.split("/api/v2/", 1)[-1].split("?", 1)[0]
        best: str | None = None
        for key in self._responses:
            if path.startswith(key) and (best is None or len(key) > len(best)):
                best = key
        if best is None:
            raise AssertionError(f"Unexpected GET {url} (path={path!r})")
        return self._responses[best]


_TEAM_PAYLOAD = {
    "teams": [
        {
            "id": "ws-1",
            "name": "Workspace",
            "members": [
                {"user": {"id": 42, "email": "dev@example.com", "username": "dev"}},
            ],
        }
    ]
}


def test_search_url_encodes_query_with_spaces() -> None:
    http = FakeHttp(
        {
            "team": _TEAM_PAYLOAD,  # _workspace()
            "team/ws-1/task": {"tasks": []},  # search_issues()
        }
    )
    provider = ClickUpProvider("test-key", http=http)

    provider.search_issues("labels detail strategies alertas")

    search_url = next(u for u in http.get_urls if "task?query=" in u)
    assert " " not in search_url
    assert "labels%20detail%20strategies%20alertas" in search_url


def test_search_url_encodes_project_id() -> None:
    http = FakeHttp({"team": _TEAM_PAYLOAD, "team/ws-1/task": {"tasks": []}})
    provider = ClickUpProvider("test-key", http=http)

    provider.search_issues("foo bar", project_id="901 713")

    search_url = next(u for u in http.get_urls if "task?query=" in u)
    assert " " not in search_url
    assert "list_ids[]=901%20713" in search_url


def test_resolve_user_reads_members_from_team_endpoint() -> None:
    http = FakeHttp({"team": _TEAM_PAYLOAD})
    provider = ClickUpProvider("test-key", http=http)

    user = provider.resolve_user_by_email("dev@example.com")

    assert user is not None
    assert user.id == "42"
    assert user.email == "dev@example.com"
    # Must not hit the non-existent team/{id}/member endpoint.
    assert not any("/member" in u for u in http.get_urls)


def test_resolve_user_returns_none_when_absent() -> None:
    http = FakeHttp({"team": _TEAM_PAYLOAD})
    provider = ClickUpProvider("test-key", http=http)

    assert provider.resolve_user_by_email("nobody@example.com") is None


def test_list_states_uses_status_name_as_id() -> None:
    http = FakeHttp(
        {
            "space/space-1/list": {"lists": [{"id": "list-1", "name": "L"}]},
            "space/space-1/folder": {"folders": []},
            "list/list-1": {
                "statuses": [
                    {"id": "p9_jVbTJxAI", "status": "to do"},
                    {"id": "p9_xyz", "status": "complete"},
                ]
            },
        }
    )
    provider = ClickUpProvider("test-key", http=http)

    states = provider.list_states("space-1")

    assert [(s.id, s.name) for s in states] == [
        ("to do", "to do"),
        ("complete", "complete"),
    ]
