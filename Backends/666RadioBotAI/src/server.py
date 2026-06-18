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


APP_NAME = "audio-only-mp3-mastering-backend"
MASTER_ADMIN_PASSWORD = os.getenv("MASTER_ADMIN_PASSWORD", "").strip()
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
