"""FastAPI-приложение FACTORIA & AI (этап 2)."""
from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from factoria.api import auth as auth_api
from factoria.api import state as state_api
from factoria.api import system as system_api
from factoria.config import Settings, get_settings
from factoria.opcua.client import OpcuaClient
from factoria.realtime.cache import TagCache
from factoria.realtime.history import HistoryWriter
from factoria.realtime.ws import router as ws_router
from factoria.seed import ensure_dev_users
from factoria.storage.db import create_all
from factoria.tags.registry import load_registry

LOG = logging.getLogger("app")


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
        LOG.info("backend запущен: env=%s, опрос OPC UA=%s", settings.env, settings.opcua_enabled)
        try:
            yield
        finally:
            if task is not None:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
            await writer.stop()

    app = FastAPI(title="FACTORIA & AI", version="0.2.0", lifespan=lifespan)
    app.state.settings = settings
    app.state.registry = registry
    app.state.cache = cache

    app.include_router(auth_api.router)
    app.include_router(state_api.router)
    app.include_router(system_api.router)
    app.include_router(ws_router)

    @app.get("/")
    async def root() -> dict[str, str]:
        return {"service": "factoria", "version": "0.2.0", "api": "/api/v1"}

    return app


app = create_app()
