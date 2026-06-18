import os
import secrets
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Request, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask


APP_NAME = "666-radiobotai-player-alert-render-backend"
MASTER_ADMIN_PASSWORD = os.getenv("MASTER_ADMIN_PASSWORD", "").strip()
PLAYER_ALERT_BACKEND_TOKEN = os.getenv("PLAYER_ALERT_BACKEND_TOKEN", "").strip()
MAX_UPLOAD_BYTES = int(os.getenv("MAX_UPLOAD_BYTES", str(50 * 1024 * 1024)))
UPLOAD_CHUNK_BYTES = 1024 * 1024
FFMPEG_TIMEOUT_SECONDS = int(os.getenv("FFMPEG_TIMEOUT_SECONDS", "120"))
ALLOWED_AUDIO_EXTENSIONS = {".mp3", ".wav", ".flac", ".m4a", ".aac", ".ogg", ".opus"}

app = FastAPI(title=APP_NAME)


# ==================================================
# HELPERS
# ==================================================
def which(binary_name: str) -> Optional[str]:
    return shutil.which(binary_name)


def check_admin(request: Request) -> None:
    if not MASTER_ADMIN_PASSWORD:
        raise HTTPException(
            status_code=500,
            detail="MASTER_ADMIN_PASSWORD not configured"
        )

    provided = request.headers.get("x-admin-password", "").strip()
    if not provided or not secrets.compare_digest(provided, MASTER_ADMIN_PASSWORD):
        raise HTTPException(status_code=401, detail="Unauthorized")


def check_player_alert_write(request: Request) -> None:
    expected = PLAYER_ALERT_BACKEND_TOKEN or MASTER_ADMIN_PASSWORD
    if not expected:
        raise HTTPException(status_code=500, detail="PLAYER_ALERT_BACKEND_TOKEN not configured")

    auth = request.headers.get("authorization", "").strip()
    bearer = auth[7:].strip() if auth.lower().startswith("bearer ") else ""
    provided = (
        request.headers.get("x-player-alert-token", "").strip()
        or bearer
        or request.headers.get("x-admin-password", "").strip()
    )
    if not provided or not secrets.compare_digest(provided, expected):
        raise HTTPException(status_code=401, detail="Unauthorized")


def cleanup_file(path_str: str) -> None:
    try:
        path = Path(path_str)
        if path.exists():
            path.unlink()
    except Exception:
        pass


def cleanup_files(*path_strs: str) -> None:
    for p in path_strs:
        cleanup_file(p)




@app.get("/")
def root():
    return {
        "ok": True,
        "service": APP_NAME,
        "routes": [
            "/health",
            "/api/player-alert/status",
            "/api/player-alert/send",
            "/api/player-alert/current",
            "/api/player-alert/history"
        ],
        "note": "Render backend relay. Secrets stay in platform environment."
    }


# ==================================================
# HEALTH
# ==================================================
@app.get("/health")
def health():
    ffmpeg_bin = which("ffmpeg")
    ffprobe_bin = which("ffprobe")

    return {
        "ok": True,
        "service": APP_NAME,
        "ffmpeg_bin": ffmpeg_bin,
        "ffmpeg_found": bool(ffmpeg_bin),
        "ffprobe_bin": ffprobe_bin,
        "ffprobe_found": bool(ffprobe_bin),
    }


# ==================================================
# PROCESS / MASTER
# ==================================================
@app.post("/process")
async def process_audio(
    request: Request,
    file: UploadFile = File(...),
    mode: str = Form(default="process"),
):
    check_admin(request)

    ffmpeg_bin = which("ffmpeg")
    if not ffmpeg_bin:
        raise HTTPException(status_code=500, detail="ffmpeg not found on server")

    original_name = file.filename or "upload.mp3"
    input_suffix = (Path(original_name).suffix or ".mp3").lower()
    if input_suffix not in ALLOWED_AUDIO_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Unsupported audio file extension")

    safe_stem = Path(original_name).stem
    output_name = f"{safe_stem}_mastered.mp3"

    # WICHTIG:
    # KEIN TemporaryDirectory() für die Rückgabedatei benutzen,
    # weil FileResponse die Datei erst NACH der Funktion sendet.
    input_tmp = tempfile.NamedTemporaryFile(delete=False, suffix=input_suffix)
    output_tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")

    input_path = Path(input_tmp.name)
    output_path = Path(output_tmp.name)

    input_tmp.close()
    output_tmp.close()

    try:
        # Upload in bounded chunks speichern, damit grosse Dateien nicht im RAM landen.
        total_bytes = 0
        with open(input_path, "wb") as f:
            while True:
                chunk = await file.read(UPLOAD_CHUNK_BYTES)
                if not chunk:
                    break
                total_bytes += len(chunk)
                if total_bytes > MAX_UPLOAD_BYTES:
                    cleanup_files(str(input_path), str(output_path))
                    raise HTTPException(status_code=413, detail="Uploaded file is too large")
                f.write(chunk)

        if total_bytes == 0:
            cleanup_files(str(input_path), str(output_path))
            raise HTTPException(status_code=400, detail="Uploaded file is empty")

        # ffmpeg mastering / loudness normalize
        cmd = [
            ffmpeg_bin,
            "-y",
            "-i", str(input_path),
            "-af", "loudnorm=I=-9:TP=-1.0:LRA=7",
            "-ar", "48000",
            "-b:a", "320k",
            str(output_path),
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=FFMPEG_TIMEOUT_SECONDS
        )

        if result.returncode != 0:
            cleanup_files(str(input_path), str(output_path))
            raise HTTPException(
                status_code=500,
                detail=f"ffmpeg failed: {result.stderr.strip() or 'unknown ffmpeg error'}"
            )

        if not output_path.exists() or output_path.stat().st_size == 0:
            cleanup_files(str(input_path), str(output_path))
            raise HTTPException(
                status_code=500,
                detail="Output file was not created"
            )

        # Input-Datei kann sofort weg
        cleanup_file(str(input_path))

        # Output-Datei erst nach dem Senden löschen
        return FileResponse(
            path=str(output_path),
            media_type="audio/mpeg",
            filename=output_name,
            background=BackgroundTask(cleanup_file, str(output_path)),
        )

    except HTTPException:
        raise

    except subprocess.TimeoutExpired:
        cleanup_files(str(input_path), str(output_path))
        raise HTTPException(status_code=504, detail="ffmpeg timed out")

    except Exception as e:
        cleanup_files(str(input_path), str(output_path))
        raise HTTPException(status_code=500, detail=str(e))


# ==================================================
# PLAYER ALERT RELAY / BROADCAST BACKEND v185
# Purpose: global backend-primary bus for WebRadio player messages.
# KV stays Worker fallback only; this backend is the primary relay.
# ==================================================
from pydantic import BaseModel
from typing import List
import time

PLAYER_ALERT_TTL_SECONDS = int(os.getenv("PLAYER_ALERT_TTL_SECONDS", "900"))
PLAYER_ALERT_MAX_HISTORY = int(os.getenv("PLAYER_ALERT_MAX_HISTORY", "30"))
_player_alert_current = None
_player_alert_history: List[dict] = []

class PlayerAlertPayload(BaseModel):
    id: str | None = None
    clientId: str | None = None
    senderId: str | None = None
    message: str
    timestamp: int | None = None
    createdAt: str | None = None
    version: str | None = None


def _clean_alert_text(value: str | None, limit: int = 240) -> str:
    text = str(value or "").replace("<", "").replace(">", "")
    text = " ".join(text.split())
    return text[:limit]


def _alert_active(alert: dict | None) -> bool:
    if not alert:
        return False
    created_ms = int(alert.get("timestamp") or 0)
    if not created_ms:
        return True
    return ((time.time() * 1000) - created_ms) < (PLAYER_ALERT_TTL_SECONDS * 1000)


@app.get("/api/player-alert/status")
def player_alert_status():
    return {
        "ok": True,
        "service": "666soundsdesign-player-alert-render-relay",
        "backend": "render",
        "ttl_seconds": PLAYER_ALERT_TTL_SECONDS,
        "history_size": len(_player_alert_history),
        "current_active": _alert_active(_player_alert_current),
    }


@app.post("/api/player-alert/send")
async def player_alert_send(request: Request, payload: PlayerAlertPayload):
    global _player_alert_current, _player_alert_history
    check_player_alert_write(request)
    message = _clean_alert_text(payload.message)
    sender = _clean_alert_text(payload.senderId or payload.clientId or "anonymous", 80) or "anonymous"
    if not message:
        raise HTTPException(status_code=400, detail="empty_message")
    now_ms = int(time.time() * 1000)
    alert = {
        "ok": True,
        "active": True,
        "id": _clean_alert_text(payload.id, 80) or f"render-{now_ms}",
        "message": message,
        "senderId": sender,
        "clientId": sender,
        "timestamp": now_ms,
        "createdAt": payload.createdAt or time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "version": _clean_alert_text(payload.version, 40),
        "source": "render-backend",
    }
    _player_alert_current = alert
    _player_alert_history.insert(0, alert)
    _player_alert_history = _player_alert_history[:PLAYER_ALERT_MAX_HISTORY]
    return {
        "ok": True,
        "delivered": True,
        "source": "render-backend",
        "alert": alert,
        "history_size": len(_player_alert_history),
    }


@app.get("/api/player-alert/current")
def player_alert_current():
    if not _alert_active(_player_alert_current):
        return {"ok": True, "active": False, "source": "render-backend"}
    return dict(_player_alert_current or {}, ok=True, active=True, source="render-backend")


@app.get("/api/player-alert/history")
def player_alert_history():
    return {
        "ok": True,
        "source": "render-backend",
        "items": _player_alert_history[:PLAYER_ALERT_MAX_HISTORY],
    }
