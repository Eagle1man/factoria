"""Лимит попыток входа (защита от перебора)."""
from __future__ import annotations

import time

from factoria.config import get_settings


class LoginLimiter:
    def __init__(self) -> None:
        self._failures: dict[str, int] = {}
        self._locked_until: dict[str, float] = {}

    def locked_for(self, username: str) -> int:
        until = self._locked_until.get(username)
        if until is None:
            return 0
        left = int(until - time.time())
        if left <= 0:
            self._locked_until.pop(username, None)
            self._failures.pop(username, None)
            return 0
        return left

    def fail(self, username: str) -> None:
        settings = get_settings()
        count = self._failures.get(username, 0) + 1
        self._failures[username] = count
        if count >= settings.login_max_failures:
            self._locked_until[username] = time.time() + settings.login_lock_min * 60

    def reset(self, username: str) -> None:
        self._failures.pop(username, None)
        self._locked_until.pop(username, None)


limiter = LoginLimiter()
