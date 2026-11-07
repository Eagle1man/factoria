"""Одноразовые тикеты для WebSocket (R-026: JWT не должен быть в URL)."""
from __future__ import annotations

import time
from dataclasses import dataclass
from uuid import uuid4


@dataclass(frozen=True)
class Ticket:
    user_id: str
    role: str
    expires_at: float


class TicketStore:
    def __init__(self) -> None:
        self._tickets: dict[str, Ticket] = {}

    def issue(self, user_id: str, role: str, ttl_s: int) -> str:
        self._cleanup()
        ticket = str(uuid4())
        self._tickets[ticket] = Ticket(user_id, role, time.time() + ttl_s)
        return ticket

    def consume(self, ticket: str) -> Ticket | None:
        self._cleanup()
        return self._tickets.pop(ticket, None)

    def _cleanup(self) -> None:
        now = time.time()
        for key in [key for key, value in self._tickets.items() if value.expires_at < now]:
            self._tickets.pop(key, None)

    @property
    def size(self) -> int:
        return len(self._tickets)


tickets = TicketStore()
