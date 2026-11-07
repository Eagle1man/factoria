"""FastAPI-приложение FACTORIA & AI (этап 2)."""
from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from factoria.api import auth as auth_api
from factoria.api import commands as commands_api
from factoria.api import orders as orders_api
from factoria.api import state as state_api
from factoria.api import system as system_api
from factoria.api import twin as twin_api
from factoria.adapters.http_ones import HttpOnesAdapter
from factoria.adapters.odata_ones import ODataOnesAdapter
from factoria.adapters.stub import StubAdapter
from factoria.config import Settings, get_settings
from factoria.opcua.client import OpcuaClient
from factoria.realtime.cache import TagCache
from factoria.realtime.events import EventBus
from factoria.realtime.history import HistoryWriter
from factoria.realtime.ws import router as ws_router
from factoria.seed import ensure_dev_users
from factoria.storage.db import create_all
from factoria.tags.registry import load_registry
from factoria.twin_scheduler import snapshot_loop

LOG = logging.getLogger("app")


def build_ones(settings):
    if settings.ones_mode == "odata":
        return ODataOnesAdapter(
            settings.ones_http_url,
            settings.ones_http_user or None,
            settings.ones_http_password or None,
        )
    if settings.ones_mode == "http":
        return HttpOnesAdapter(
            settings.ones_http_url,
            settings.ones_http_user or None,
            settings.ones_http_password or None,
        )
    return StubAdapter()


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    registry = load_registry()
    cache = TagCache(registry)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        writer = HistoryWriter()
        app.state.history = writer
        if settings.env in {"dev", "test"}:
            await create_all()
            await ensure_dev_users()

        writer.start()
        task: asyncio.Task | None = None
        if settings.opcua_enabled:
            client = OpcuaClient(
                cache,
                writer,
                endpoint=settings.opcua_endpoint,
                namespace=registry.namespace,
                tags=tuple(t.id for t in registry.tags),
            )
            task = asyncio.create_task(client.run(), name="opcua-client")

        twin_task: asyncio.Task | None = None
        if settings.twin_snapshot_minutes > 0 and settings.env in {"dev", "pilot"}:
            twin_task = asyncio.create_task(
                snapshot_loop(
                    registry,
                    cache,
                    app.state.ones,
                    settings.twin_snapshot_minutes * 60,
                ),
                name="twin-snapshots",
            )
            LOG.info("снимки двойника каждые %s мин", settings.twin_snapshot_minutes)

        LOG.info("backend запущен: env=%s, опрос OPC UA=%s", settings.env, settings.opcua_enabled)
        if settings.opcua_security == "None" and settings.env != "dev":
            LOG.warning(
                "OPC UA без шифрования (SecurityPolicy None) в среде %s: "
                "до пилота включите Basic256Sha256 (docs/security/ot-baseline.md)",
                settings.env,
            )
        try:
            yield
        finally:
            for background in (task, twin_task):
                if background is not None:
                    background.cancel()
                    try:
                        await background
                    except asyncio.CancelledError:
                        pass
            await writer.stop()

    app = FastAPI(title="FACTORIA & AI", version="0.2.0", lifespan=lifespan)
    app.state.settings = settings
    app.state.registry = registry
    app.state.cache = cache
    app.state.events = EventBus()
    app.state.ones = build_ones(settings)

    app.include_router(auth_api.router)
    app.include_router(state_api.router)
    app.include_router(system_api.router)
    app.include_router(commands_api.router)
    app.include_router(orders_api.router)
    app.include_router(twin_api.router)
    app.include_router(ws_router)

    @app.get("/")
    async def root() -> dict[str, str]:
        return {"service": "factoria", "version": "0.2.0", "api": "/api/v1"}

    return app


app = create_app()
