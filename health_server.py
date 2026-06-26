from __future__ import annotations

import logging
import os
import time
from typing import Callable, Awaitable, Any

from aiohttp import web

logger = logging.getLogger("666RadioBotAI.health")


class HealthServer:
    def __init__(self, status_provider: Callable[[], dict[str, Any]]):
        self.status_provider = status_provider
        self.host = os.getenv("HEALTH_HOST", "0.0.0.0")
        self.port = int(os.getenv("HEALTH_PORT") or os.getenv("PORT") or "8080")
        self.started_at = time.time()
        self.runner: web.AppRunner | None = None

    async def start(self) -> None:
        if self.runner is not None:
            return
        app = web.Application()
        app.router.add_get("/healthz", self.healthz)
        app.router.add_get("/readyz", self.readyz)
        app.router.add_get("/", self.root)
        self.runner = web.AppRunner(app, access_log=None)
        await self.runner.setup()
        site = web.TCPSite(self.runner, self.host, self.port)
        await site.start()
        logger.info("Healthcheck aktiv auf %s:%s", self.host, self.port)

    async def stop(self) -> None:
        if self.runner:
            await self.runner.cleanup()
            self.runner = None

    async def root(self, request: web.Request) -> web.Response:
        return web.json_response({
            "service": "666SOUNDsDESIGn RadioBotAI Hybrid",
            "health": "/healthz",
            "ready": "/readyz",
        })

    async def healthz(self, request: web.Request) -> web.Response:
        data = self.status_provider()
        data["uptime_seconds"] = int(time.time() - self.started_at)
        return web.json_response(data, status=200)

    async def readyz(self, request: web.Request) -> web.Response:
        data = self.status_provider()
        ready = bool(data.get("discord_ready"))
        return web.json_response(data, status=200 if ready else 503)
