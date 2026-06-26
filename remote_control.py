from __future__ import annotations

import json
import logging
import os
import ssl
import time
from dataclasses import dataclass
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import aiohttp

logger = logging.getLogger("666RadioBotAI.remote")


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on", "ja"}


@dataclass
class SkipResult:
    ok: bool
    message: str
    status: int | None = None
    data: Any = None
    route: str = ""


class RemoteAutoDJController:
    """Geschützter Remote-Skip-Treiber für den 666 RadioBotAI.

    Primärpfad:
        Discord Bot -> RadioBotAI Worker -> Admin Worker -> SHOUTcast/AutoDJ

    Optionale Fallbacks:
        - Direkter Admin-Worker-Aufruf, erst nach expliziter Aktivierung.
        - Frei konfigurierbarer HTTP-Endpunkt.
        - Direkter SHOUTcast ``kicksrc``-Aufruf.

    Tokens, Passwörter und Gate-Codes werden ausschließlich aus der Umgebung
    gelesen und niemals in Statusmeldungen oder Logs ausgegeben.
    """

    def __init__(self) -> None:
        self.mode = os.getenv("AUTO_DJ_SKIP_MODE", "worker").strip().lower()

        self.worker_base_url = os.getenv(
            "RADIOBOTAI_WORKER_URL",
            "https://666radiobotai.666soundsdesign-broadcaster.com",
        ).strip().rstrip("/")
        self.worker_skip_path = os.getenv("RADIOBOTAI_WORKER_SKIP_PATH", "/radio/autodj/skip").strip()
        self.worker_status_path = os.getenv("RADIOBOTAI_WORKER_STATUS_PATH", "/radio/autodj/status").strip()
        self.worker_token = (
            os.getenv("RADIOBOTAI_WORKER_TOKEN", "")
            or os.getenv("DISCORD_ADMIN_TOKEN", "")
            or os.getenv("ADMIN_TOKEN", "")
        )
        self.worker_gate = os.getenv("RADIOBOTAI_WORKER_GATE_CODE", "")

        self.admin_worker_url = os.getenv(
            "RADIO_ADMIN_WORKER_URL",
            "https://666myidjstreamadmin.666soundsdesign-broadcaster.com",
        ).strip().rstrip("/")
        self.admin_worker_fallback_url = os.getenv(
            "RADIO_ADMIN_WORKER_FALLBACK_URL",
            "https://666myidjstreamadmin.digital-underground-connected.workers.dev",
        ).strip().rstrip("/")
        self.admin_worker_skip_path = os.getenv("RADIO_ADMIN_WORKER_SKIP_PATH", "/admin/autodj/skip").strip()
        self.admin_worker_token = os.getenv("RADIO_ADMIN_WORKER_TOKEN", "") or self.worker_token
        self.direct_admin_fallback = _env_bool("RADIO_ADMIN_DIRECT_FALLBACK", False)

        self.custom_url = os.getenv("AUTO_DJ_SKIP_URL", "").strip()
        self.method = os.getenv("AUTO_DJ_SKIP_METHOD", "POST").strip().upper()
        self.username = os.getenv("AUTO_DJ_ADMIN_USER", "").strip()
        self.password = os.getenv("AUTO_DJ_ADMIN_PASSWORD", "")
        self.admin_url = os.getenv("SHOUTCAST_ADMIN_URL", "").strip()
        self.sid = os.getenv("SHOUTCAST_SID", "1").strip() or "1"
        self.verify_ssl = _env_bool("AUTO_DJ_VERIFY_SSL", True)
        self.password_in_query = _env_bool("SHOUTCAST_PASSWORD_IN_QUERY", False)
        self.timeout = max(3, int(os.getenv("AUTO_DJ_HTTP_TIMEOUT", "12")))
        self.cooldown = max(0, int(os.getenv("AUTO_DJ_SKIP_COOLDOWN", "8")))
        self.success_text = os.getenv("AUTO_DJ_SKIP_SUCCESS_TEXT", "").strip().lower()
        self.headers = self._parse_json_env("AUTO_DJ_SKIP_HEADERS_JSON", {})
        self.body = self._parse_json_env("AUTO_DJ_SKIP_BODY_JSON", {})
        self.last_skip_at = 0.0

    @staticmethod
    def _parse_json_env(name: str, default: Any) -> Any:
        raw = os.getenv(name, "").strip()
        if not raw:
            return default
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            logger.warning("%s enthält ungültiges JSON und wird ignoriert.", name)
            return default

    @property
    def enabled(self) -> bool:
        if self.mode == "worker":
            return bool(self.worker_base_url)
        if self.mode == "custom":
            return bool(self.custom_url)
        if self.mode == "shoutcast_kicksrc":
            return bool(self.admin_url)
        return False

    @property
    def protected(self) -> bool:
        if self.mode == "worker":
            return bool(self.worker_token or self.worker_gate)
        if self.mode in {"custom", "shoutcast_kicksrc"}:
            return bool(self.password or self.username or self.headers)
        return False

    @staticmethod
    def _host(url: str) -> str:
        return urlsplit(url).netloc if url else "nicht gesetzt"

    def masked_summary(self) -> str:
        if not self.enabled:
            return "deaktiviert"
        if self.mode == "worker":
            protection = "geschützt" if self.protected else "Token fehlt"
            fallback = "direkter Admin-Fallback ON" if self.direct_admin_fallback else "direkter Admin-Fallback OFF"
            return f"worker -> {self._host(self.worker_base_url)} ({protection}; {fallback})"
        target = self.custom_url if self.mode == "custom" else self.admin_url
        protection = "geschützt" if self.protected else "Zugang fehlt"
        return f"{self.mode} -> {self._host(target)} ({protection})"

    async def skip(self) -> SkipResult:
        if not self.enabled:
            return SkipResult(False, "Remote-/skip ist nicht konfiguriert.")
        if self.mode == "worker" and not self.protected:
            return SkipResult(False, "Worker-Skip ist vorbereitet, aber RADIOBOTAI_WORKER_TOKEN oder GATE_CODE fehlt.")

        now = time.monotonic()
        remaining = self.cooldown - (now - self.last_skip_at)
        if remaining > 0:
            return SkipResult(False, f"Skip-Schutz aktiv. Noch {remaining:.1f} Sekunden warten.")

        if self.mode == "worker":
            result = await self._worker_skip()
        elif self.mode == "custom":
            result = await self._custom_skip()
        elif self.mode == "shoutcast_kicksrc":
            result = await self._shoutcast_kicksrc()
        else:
            return SkipResult(False, f"Unbekannter AUTO_DJ_SKIP_MODE: {self.mode}")

        if result.ok:
            self.last_skip_at = time.monotonic()
        return result

    async def status(self) -> dict[str, Any]:
        base: dict[str, Any] = {
            "enabled": self.enabled,
            "mode": self.mode,
            "protected": self.protected,
            "target": self.masked_summary(),
            "primary_worker_host": self._host(self.worker_base_url),
            "admin_worker_host": self._host(self.admin_worker_url),
            "admin_worker_fallback_host": self._host(self.admin_worker_fallback_url),
            "direct_admin_fallback": self.direct_admin_fallback,
        }
        if self.mode != "worker" or not self.worker_base_url:
            return base
        result = await self._request(
            "GET",
            self.worker_base_url + self._path(self.worker_status_path),
            headers=self._worker_headers(),
            route="radiobotai-worker-status",
        )
        base.update({
            "reachable": result.ok,
            "http_status": result.status,
            "worker": result.data if result.ok else None,
        })
        return base

    @staticmethod
    def _path(value: str) -> str:
        return "/" + value.lstrip("/")

    def _ssl_context(self) -> ssl.SSLContext | bool:
        return True if self.verify_ssl else False

    def _auth(self) -> aiohttp.BasicAuth | None:
        if self.username or self.password:
            return aiohttp.BasicAuth(self.username or "admin", self.password)
        return None

    def _worker_headers(self) -> dict[str, str]:
        headers = {"content-type": "application/json", "user-agent": "666RadioBotAI-Hybrid/3.3"}
        if self.worker_token:
            headers["x-admin-token"] = self.worker_token
            headers["authorization"] = f"Bearer {self.worker_token}"
        if self.worker_gate:
            headers["x-discord-gate-code"] = self.worker_gate
        return headers

    def _admin_worker_headers(self) -> dict[str, str]:
        headers = {"content-type": "application/json", "user-agent": "666RadioBotAI-Hybrid/3.3"}
        if self.admin_worker_token:
            headers["x-admin-token"] = self.admin_worker_token
            headers["authorization"] = f"Bearer {self.admin_worker_token}"
        return headers

    async def _request(
        self,
        method: str,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        json_body: Any = None,
        headers: dict[str, str] | None = None,
        use_basic_auth: bool = False,
        route: str = "",
    ) -> SkipResult:
        timeout = aiohttp.ClientTimeout(total=self.timeout)
        merged_headers = dict(self.headers)
        merged_headers.update(headers or {})
        auth = self._auth() if use_basic_auth else None
        try:
            async with aiohttp.ClientSession(timeout=timeout, headers=merged_headers, auth=auth) as session:
                async with session.request(
                    method,
                    url,
                    params=params,
                    json=json_body,
                    ssl=self._ssl_context(),
                    allow_redirects=True,
                ) as response:
                    text = (await response.text(errors="replace"))[:4000]
                    try:
                        data = json.loads(text) if text else None
                    except json.JSONDecodeError:
                        data = text[:1000]
                    ok = 200 <= response.status < 300
                    if ok and self.success_text:
                        ok = self.success_text in text.lower()
                    if ok:
                        return SkipResult(True, "AutoDJ-Skip wurde erfolgreich gesendet.", response.status, data, route)
                    detail = ""
                    if isinstance(data, dict):
                        detail = str(data.get("error") or data.get("message") or "")[:180]
                    return SkipResult(
                        False,
                        f"Remote-Server antwortete mit HTTP {response.status}" + (f": {detail}" if detail else "."),
                        response.status,
                        data,
                        route,
                    )
        except aiohttp.ClientError as exc:
            logger.warning("Remote-Skip über %s fehlgeschlagen: %s", route or "unbekannte Route", type(exc).__name__)
            return SkipResult(False, f"Verbindung zum AutoDJ-Server fehlgeschlagen: {type(exc).__name__}.", route=route)
        except Exception as exc:
            logger.exception("Unerwarteter Remote-Skip-Fehler über %s", route or "unbekannte Route")
            return SkipResult(False, f"Remote-Skip-Fehler: {type(exc).__name__}.", route=route)

    async def _worker_skip(self) -> SkipResult:
        payload = {"action": "skip", "source": "666radiobotai-discord-hybrid-v3.3"}
        primary = await self._request(
            "POST",
            self.worker_base_url + self._path(self.worker_skip_path),
            json_body=payload,
            headers=self._worker_headers(),
            route="radiobotai-worker",
        )
        if primary.ok:
            primary.message = "AutoDJ-Skip über den RadioBotAI Worker wurde erfolgreich gesendet."
            return primary

        if not self.direct_admin_fallback:
            primary.message += " Direkter Admin-Worker-Fallback ist aus Sicherheitsgründen deaktiviert."
            return primary

        if not self.admin_worker_token:
            primary.message += " Admin-Worker-Fallback ist aktiviert, aber RADIO_ADMIN_WORKER_TOKEN fehlt."
            return primary

        targets: list[tuple[str, str]] = []
        if self.admin_worker_url:
            targets.append(("admin-worker-custom-domain", self.admin_worker_url))
        if self.admin_worker_fallback_url and self.admin_worker_fallback_url != self.admin_worker_url:
            targets.append(("admin-worker-workers-dev", self.admin_worker_fallback_url))

        failures: list[str] = []
        for route, base_url in targets:
            fallback = await self._request(
                "POST",
                base_url + self._path(self.admin_worker_skip_path),
                json_body=payload,
                headers=self._admin_worker_headers(),
                route=route,
            )
            if fallback.ok:
                fallback.message = "AutoDJ-Skip über den direkten Admin-Worker-Fallback wurde erfolgreich gesendet."
                return fallback
            failures.append(f"{route}: HTTP {fallback.status or 0}")

        primary.message += " Admin-Worker-Fallback ebenfalls fehlgeschlagen" + (f" ({'; '.join(failures)})." if failures else ".")
        return primary

    async def _custom_skip(self) -> SkipResult:
        if not self.custom_url:
            return SkipResult(False, "AUTO_DJ_SKIP_URL fehlt.")
        if self.method not in {"GET", "POST", "PUT", "PATCH"}:
            return SkipResult(False, f"Nicht erlaubte HTTP-Methode: {self.method}.")
        if self.method == "GET":
            return await self._request("GET", self.custom_url, params=self.body or None, use_basic_auth=True, route="custom")
        return await self._request(self.method, self.custom_url, json_body=self.body or None, use_basic_auth=True, route="custom")

    async def _shoutcast_kicksrc(self) -> SkipResult:
        if not self.admin_url:
            return SkipResult(False, "SHOUTCAST_ADMIN_URL fehlt.")
        parts = urlsplit(self.admin_url)
        path = parts.path or "/admin.cgi"
        if not path.endswith("admin.cgi"):
            path = path.rstrip("/") + "/admin.cgi"
        query = dict(parse_qsl(parts.query, keep_blank_values=True))
        query.update({"mode": "kicksrc", "sid": self.sid})
        if self.password_in_query and self.password:
            query["pass"] = self.password
        url = urlunsplit((parts.scheme, parts.netloc, path, urlencode(query), parts.fragment))
        return await self._request("GET", url, use_basic_auth=True, route="shoutcast-kicksrc")
