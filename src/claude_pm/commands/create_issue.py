"""`create-issue` — create a single issue with optional assignee + labels."""

from __future__ import annotations

import argparse
from dataclasses import replace
from pathlib import Path

from ..application.issue_creation import CreateIssueService
from ..application.setup_flow import SetupService
from ..config import Config
from ..exceptions import EXIT_OK, NeedsChoice, PMError
from ._helpers import build_provider, get_cache_repo, print_json


def run(args: argparse.Namespace) -> int:
    config = Config.load(args.repo_name)
    provider = build_provider(config)
    cache_repo = get_cache_repo(config)
    cache = SetupService(provider, cache_repo, config).ensure()

    # Resolve which project to use
    projects = cache.projects
    project_id_override = getattr(args, "project_id", None)
    if len(projects) > 1 and not project_id_override:
        raise NeedsChoice(
            "Multiple projects configured. Re-run with --project-id <ID>.",
            {"action": "choose-project", "projects": list(projects)},
        )
    if project_id_override:
        matched = next((p for p in projects if p["id"] == project_id_override), None)
        cache = replace(
            cache,
            project_id=project_id_override,
            project_name=matched["name"] if matched else project_id_override,
        )

    if args.description_file:
        description_path = Path(args.description_file).expanduser()
        if not description_path.is_file():
            raise PMError(f"Description file not found: {description_path}")
        description = description_path.read_text(encoding="utf-8")
    elif args.description:
        description = args.description
    else:
        raise PMError("Either --description or --description-file is required.")

    issue = CreateIssueService(provider, cache).create(
        title=args.title,
        description=description,
        state_name=args.state,
        priority=args.priority,
        assignee_email=args.assignee,
        label_names=args.label or [],
    )
    print_json(
        {
            "ok": True,
            "id": issue.identifier,
            "identifier": issue.identifier,
            "title": issue.title,
            "url": issue.url,
        }
    )
    return EXIT_OK
