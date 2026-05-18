"""`create-doc` / `update-doc` — ClickUp Docs via v3 API."""

from __future__ import annotations

import argparse
from pathlib import Path

from ..config import Config
from ..exceptions import EXIT_OK, PMError
from ..infrastructure.providers.clickup import ClickUpProvider
from ._helpers import build_provider, print_json


def run_create_doc(args: argparse.Namespace) -> int:
    config = Config.load(args.repo_name)
    provider = build_provider(config)
    if not isinstance(provider, ClickUpProvider):
        raise PMError("create-doc is only supported for ClickUp projects.")
    content: str | None = None
    if args.content_file:
        path = Path(args.content_file).expanduser()
        if not path.is_file():
            raise PMError(f"Content file not found: {path}")
        content = path.read_text(encoding="utf-8")
    doc = provider.create_doc(args.title, content)
    print_json(
        {
            "ok": True,
            "id": doc.id,
            "title": doc.title,
            "url": doc.url,
            "note": "Doc created at workspace level (List association not supported by ClickUp API).",
        }
    )
    return EXIT_OK


def run_update_doc(args: argparse.Namespace) -> int:
    config = Config.load(args.repo_name)
    provider = build_provider(config)
    if not isinstance(provider, ClickUpProvider):
        raise PMError("update-doc is only supported for ClickUp projects.")
    content: str | None = None
    if args.content_file:
        path = Path(args.content_file).expanduser()
        if not path.is_file():
            raise PMError(f"Content file not found: {path}")
        content = path.read_text(encoding="utf-8")
    doc = provider.update_doc(
        args.doc_id,
        title=args.title,
        content=content,
        page_id=args.page_id,
    )
    print_json({"ok": True, "id": doc.id, "title": doc.title, "url": doc.url})
    return EXIT_OK
