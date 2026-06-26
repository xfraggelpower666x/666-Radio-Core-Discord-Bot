from __future__ import annotations

import logging
import os
import ssl
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlsplit

import aiohttp

logger = logging.getLogger("666RadioBotAI.alert")


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on", "ja"}


@dataclass
class AlertResult:
    ok: bool
    message: str
    status: int | None = None
    data: Any = None
    route: str = ""


class RadioAlertBridge:
    """Geschützte Radio-/Player-Alert-Bridge.

    Primärpfad:
        Discord Bot -> Cloudflare RadioBotAI Worker -> Render Alert Backend

    Optionaler Fallback:
        Discord Bot -> Render Alert Backend direkt

    Sämtliche Tokens werden nur aus Umgebungsvariablen gelesen und niemals
    in Antworten oder Logs ausgegeben.
    """

    def __init__(self) -> None:
        self.worker_base_url = os.getenv(
            "PLAYER_ALERT_WORKER_URL",
            os.getenv(
                "RADIOBOTAI_WORKER_URL",
                "https://666radiobotai.666soundsdesign-broadcaster.com",
            ),
        ).strip().rstrip("/")
        self.worker_send_path = os.getenv("PLAYER_ALERT_SEND_PATH", "/api/player-alert/send").strip()
        self.worker_status_path = os.getenv("PLAYER_ALERT_STATUS_PATH", "/api/player-alert/status").strip()
        self.worker_current_path = os.getenv("PLAYER_ALERT_CURRENT_PATH", "/api/player-alert/current").strip()
        self.worker_history_path = os.getenv("PLAYER_ALERT_HISTORY_PATH", "/api/player-alert/history").strip()
        self.worker_render_status_path = os.getenv("PLAYER_ALERT_RENDER_STATUS_PATH", "/render/status").strip()
        self.worker_token = (
            os.getenv("PLAYER_ALERT_WORKER_TOKEN", "")
            or os.getenv("RADIOBOTAI_WORKER_TOKEN", "")
            or os.getenv("DISCORD_ADMIN_TOKEN", "")
            or os.getenv("ADMIN_TOKEN", "")
        )
        self.worker_gate = os.getenv("PLAYER_ALERT_GATE_CODE", "") or os.getenv("RADIOBOTAI_WORKER_GATE_CODE", "")

        self.backend_base_url = os.getenv("PLAYER_ALERT_DIRECT_BACKEND_URL", "").strip().rstrip("/")
        self.backend_token = os.getenv("PLAYER_ALERT_BACKEND_TOKEN", "") or os.getenv("PLAYER_ALERT_TOKEN", "")
        self.direct_fallback = _env_bool("PLAYER_ALERT_DIRECT_FALLBACK", False)

        self.username = os.getenv("PLAYER_ALERT_USERNAME", "666 RadioBotAI").strip()[:28] or "666 RadioBotAI"
        self.timeout = max(3, int(os.getenv("PLAYER_ALERT_HTTP_TIMEOUT", "12")))
        self.verify_ssl = _env_bool("PLAYER_ALERT_VERIFY_SSL", True)

    @staticmethod
    def _path(value: str) -> str:
        return "/" + value.lstrip("/")

    @staticmethod
    def _host(url: str) -> str:
        return urlsplit(url).netloc if url else "nicht gesetzt"

    def _ssl_context(self) -> ssl.SSLContext | bool:
        return True if self.verify_ssl else False

    @property
    def enabled(self) -> bool:
        return bool(self.worker_base_url)

    @property
    def protected(self) -> bool:
        return bool(self.worker_token or self.worker_gate)

    def masked_summary(self) -> str:
        if not self.enabled:
            return "deaktiviert"
        protection = "geschützt" if self.protected else "Token/Gate fehlt"
        fallback = "Render-Fallback ON" if self.direct_fallback else "Render-Fallback OFF"
        return f"worker -> {self._host(self.worker_base_url)} ({protection}; {fallback})"

    def _worker_headers(self) -> dict[str, str]:
        headers = {
            "content-type": "application/json",
            "user-agent": "666RadioBotAI-Hybrid/3.3",
        }
        if self.worker_token:
            headers["x-admin-token"] = self.worker_token
            headers["authorization"] = f"Bearer {self.worker_token}"
        if self.worker_gate:
            headers["x-discord-gate-code"] = self.worker_gate
        return headers

    def _backend_headers(self) -> dict[str, str]:
        headers = {
            "content-type": "application/json",
            "user-agent": "666RadioBotAI-Hybrid/3.3",
        }
        if self.backend_token:
            headers["x-player-alert-token"] = self.backend_token
        return headers

    def _backend_endpoint(self, action: str) -> str:
        base = self.backend_base_url.rstrip("/")
        if base.endswith("/api/player-alert"):
            return f"{base}/{action.lstrip('/')}"
        return f"{base}/api/player-alert/{action.lstrip('/')}"

    async def _request(
        self,
        method: str,
        url: str,
        *,
        headers: dict[str, str] | None = None,
        json_body: dict[str, Any] | None = None,
        route: str,
    ) -> AlertResult:
        timeout = aiohttp.ClientTimeout(total=self.timeout)
        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.request(
                    method,
                    url,
                    headers=headers or {},
                    json=json_body,
                    ssl=self._ssl_context(),
                ) as response:
                    text = await response.text()
                    try:
                        data: Any = await response.json(content_type=None)
                    except Exception:
                        data = text[:1200]
                    ok = 200 <= response.status < 300
                    if ok:
                        return AlertResult(True, "Radio-Alert erfolgreich verarbeitet.", response.status, data, route)
                    if response.status == 401:
                        message = "Radio-Alert abgelehnt: Auth-Token oder Gate-Code ungültig/fehlend."
                    elif response.status == 429:
                        retry_ms = data.get("retryAfterMs") if isinstance(data, dict) else None
                        message = "Radio-Alert Rate-Limit aktiv."
                        if retry_ms:
                            message += f" Noch ca. {max(1, int(retry_ms) // 1000)} Sekunden warten."
                    else:
                        message = f"Radio-Alert HTTP-Fehler {response.status}."
                    return AlertResult(False, message, response.status, data, route)
        except aiohttp.ClientError as exc:
            logger.warning("Radio-Alert-Verbindungsfehler auf Route %s: %s", route, type(exc).__name__)
            return AlertResult(False, f"Radio-Alert-Verbindungsfehler: {type(exc).__name__}.", route=route)
        except Exception as exc:
            logger.exception("Unerwarteter Radio-Alert-Fehler auf Route %s", route)
            return AlertResult(False, f"Radio-Alert-Fehler: {type(exc).__name__}.", route=route)

    async def send(
        self,
        message: str,
        *,
        sender_id: str,
        source: str = "discord",
        metadata: dict[str, Any] | None = None,
    ) -> AlertResult:
        clean_message = " ".join(str(message or "").replace("<", "").replace(">", "").split())[:240]
        if not clean_message:
            return AlertResult(False, "Radio-Alert-Nachricht ist leer.")
        if not self.enabled:
            return AlertResult(False, "Radio-Alert-Worker ist nicht konfiguriert.")
        if not self.protected:
            return AlertResult(False, "Radio-Alert ist vorbereitet, aber PLAYER_ALERT_WORKER_TOKEN oder Gate-Code fehlt.")

        payload: dict[str, Any] = {
            "message": clean_message,
            "username": self.username,
            "senderId": str(sender_id)[:80],
            "source": source,
            "version": "v3.3.0",
        }
        if metadata:
            payload.update({key: value for key, value in metadata.items() if value is not None})

        primary = await self._request(
            "POST",
            self.worker_base_url + self._path(self.worker_send_path),
            headers=self._worker_headers(),
            json_body=payload,
            route="radiobotai-worker-player-alert",
        )
        if primary.ok:
            primary.message = "Radio-Alert wurde über den RadioBotAI Worker an den Alert-Service gesendet."
            return primary

        if not self.direct_fallback:
            primary.message += " Direkter Render-Fallback ist deaktiviert."
            return primary
        if not self.backend_base_url:
            primary.message += " PLAYER_ALERT_DIRECT_BACKEND_URL fehlt."
            return primary
        if not self.backend_token:
            primary.message += " PLAYER_ALERT_BACKEND_TOKEN fehlt."
            return primary

        fallback = await self._request(
            "POST",
            self._backend_endpoint("send"),
            headers=self._backend_headers(),
            json_body=payload,
            route="render-player-alert-direct",
        )
        if fallback.ok:
            fallback.message = "Radio-Alert wurde über den direkten Render-Fallback gesendet."
        return fallback

    async def status(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "enabled": self.enabled,
            "protected": self.protected,
            "route": self.masked_summary(),
            "worker_host": self._host(self.worker_base_url),
            "backend_host": self._host(self.backend_base_url),
            "direct_fallback": self.direct_fallback,
        }
        if not self.enabled:
            return result

        worker = await self._request(
            "GET",
            self.worker_base_url + self._path(self.worker_status_path),
            headers=self._worker_headers(),
            route="player-alert-status",
        )
        render = await self._request(
            "GET",
            self.worker_base_url + self._path(self.worker_render_status_path),
            headers=self._worker_headers(),
            route="render-status",
        )
        result.update({
            "worker_reachable": worker.ok,
            "worker_http_status": worker.status,
            "worker": worker.data if worker.ok else None,
            "render_status_reachable": render.ok,
            "render_http_status": render.status,
            "render": render.data if render.ok else None,
        })
        return result

    async def current(self) -> AlertResult:
        return await self._request(
            "GET",
            self.worker_base_url + self._path(self.worker_current_path),
            headers=self._worker_headers(),
            route="player-alert-current",
        )

    async def history(self) -> AlertResult:
        return await self._request(
            "GET",
            self.worker_base_url + self._path(self.worker_history_path),
            headers=self._worker_headers(),
            route="player-alert-history",
        )
