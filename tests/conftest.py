from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend" / "src"))

# Окружение задаётся ДО импорта factoria: настройки кэшируются при импорте.
os.environ.setdefault("ENV", "test")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./data/test_factoria.db")
os.environ.setdefault("OPCUA_ENABLED", "false")
os.environ.setdefault("JWT_SECRET", "test-secret-at-least-32-bytes-long!!")

DB_FILE = ROOT / "data" / "test_factoria.db"
if DB_FILE.exists():
    DB_FILE.unlink()
