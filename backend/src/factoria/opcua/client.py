"""Клиент OPC UA: чтение тегов, качество, переподключение (ТЗ §5.1, DoD §5.7).

Подписка (subscription) заменена циклом чтения всех тегов раз в интервал:
21 чтение за такт даёт задержку < 1 c, чего достаточно для DoD «q=bad ≤ 3 c»,
и убирает проблему «статичный тег стареет, потому что нет data change».
"""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone

from asyncua import Client, ua
from asyncua.crypto.security_policies import SecurityPolicyBasic256Sha256

from factoria.realtime.cache import BAD, GOOD, TagCache

LOG = logging.getLogger("opcua-client")
BACKOFF = (1, 2, 5, 10)


class OpcuaClient:
    def __init__(
        self,
        cache: TagCache,
        history,
        *,
        endpoint: str,
        namespace: str,
        tags: tuple[str, ...],
        interval_s: float = 0.5,
        security: str = "None",
        client_cert: str = "",
        client_key: str = "",
        server_cert: str = "",
    ) -> None:
        self.cache = cache
        self.history = history
        self.endpoint = endpoint
        self.namespace = namespace
        self.tags = tags
        self.interval_s = interval_s
        self.security = security
        self.client_cert = client_cert
        self.client_key = client_key
        self.server_cert = server_cert

    async def run(self) -> None:
        attempt = 0
        while True:
            try:
                await self._watch()
                attempt = 0
            except asyncio.CancelledError:
                raise
            except Exception as exc:  # noqa: BLE001 - любой обрыв = BAD и реконнект
                LOG.warning("OPC UA недоступен: %s", exc)
                self.cache.mark_source_down()
                delay = BACKOFF[min(attempt, len(BACKOFF) - 1)]
                attempt += 1
                await asyncio.sleep(delay)

    async def _watch(self) -> None:
        client = Client(self.endpoint)
        if self.security and self.security != "None":
            mode = (
                ua.MessageSecurityMode.Sign
                if self.security == "Basic256Sha256_Sign"
                else ua.MessageSecurityMode.SignAndEncrypt
            )
            await client.set_security(
                SecurityPolicyBasic256Sha256,
                self.client_cert,
                self.client_key,
                server_certificate=self.server_cert,
                mode=mode,
            )
        async with client:
            index = await client.get_namespace_index(self.namespace)
            nodes = [client.get_node(f"ns={index};s={tag}") for tag in self.tags]
            self.cache.mark_source_up()
            LOG.info("подключено к %s, тегов %d", self.endpoint, len(nodes))

            while True:
                values = await client.read_attributes(nodes, ua.AttributeIds.Value)
                now = datetime.now(timezone.utc)
                for tag, dv in zip(self.tags, values, strict=True):
                    quality = GOOD if dv.StatusCode.is_good() else BAD
                    ts = dv.SourceTimestamp or now
                    if ts.tzinfo is None:
                        ts = ts.replace(tzinfo=timezone.utc)
                    self.cache.update(tag, dv.Value.Value, quality=quality, ts=ts)
                    self.history.offer(tag, dv.Value.Value, quality, ts)
                await asyncio.sleep(self.interval_s)
