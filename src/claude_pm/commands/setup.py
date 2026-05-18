"""`setup` — discover team/project/states and write the cache."""

from __future__ import annotations

import argparse

from ..application.setup_flow import SetupOptions, SetupService
from ..config import Config
from ..exceptions import EXIT_OK
from ._helpers import build_provider, get_cache_repo, print_json


def run(args: argparse.Namespace) -> int:
    config = Config.load(args.repo_name)
    provider = build_provider(config)
    cache_repo = get_cache_repo(config)

    options = SetupOptions(
        force=args.force,
        team_id_override=args.team_id,
        project_id_override=args.project_id,
        create_project_if_missing=args.create_project,
    )
    cache = SetupService(provider, cache_repo, config).ensure(options)

    print_json({
        "ok": True,
        "cache": {
            "team_id": cache.team_id,
            "project_id": cache.project_id,
            "project_name": cache.project_name,
            "projects": list(cache.projects),
            "state_ids": cache.state_ids,
            "last_refresh": cache.last_refresh,
        },
        "cache_path": str(cache_repo.path),
    })
    return EXIT_OK
