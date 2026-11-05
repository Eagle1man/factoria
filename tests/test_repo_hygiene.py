"""Гигиена репозитория: конфиги не должны содержать BOM.

configparser (alembic.ini) и tomllib падают на BOM в начале файла,
а редакторы Windows добавляют его молча.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SUFFIXES = {".py", ".md", ".ts", ".ini", ".toml", ".yaml", ".yml", ".jsonc", ".mako", ".mako"}
SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "data"}


def _files():
    for path in ROOT.rglob("*"):
        if path.is_dir() or any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.suffix.lower() in SUFFIXES or path.name.startswith(".env"):
            yield path


def test_no_bom_in_repository():
    offenders = [
        str(path.relative_to(ROOT))
        for path in _files()
        if path.read_bytes()[:3] == b"\xef\xbb\xbf"
    ]
    assert offenders == [], f"BOM найден: {offenders}"
