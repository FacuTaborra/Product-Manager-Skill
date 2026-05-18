"""`get-issue` — fetch a single issue by ID, including its description."""

from __future__ import annotations

import argparse

from ..application.setup_flow import SetupService
from ..config import Config
from ..exceptions import EXIT_OK
from ._helpers import build_provider, load_cache, print_json


def run(args: argparse.Namespace) -> int:
    config = Config.load(args.repo_name)
    provider = build_provider(config)
    SetupService(provider, load_cache(config), config).ensure()

    issue = provider.get_issue(args.id)
    print_json({
        "id": issue.identifier,
        "title": issue.title,
        "description": issue.description,
        "state": {"id": issue.state.id, "name": issue.state.name},
        "priority": issue.priority,
        "url": issue.url,
        "project": (
            {"id": issue.project.id, "name": issue.project.name} if issue.project else None
        ),
    })
    return EXIT_OK
