from __future__ import annotations

import json
import os
import shutil
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]


def result(ok: bool, label: str, detail: str = "") -> bool:
    marker = "PASS" if ok else "FAIL"
    print(f"[{marker}] {label}" + (f": {detail}" if detail else ""))
    return ok


def main() -> int:
    checks: list[bool] = []
    checks.append(result(sys.version_info >= (3, 11), "Python >= 3.11", sys.version.split()[0]))
    checks.append(result(bool(shutil.which("ffmpeg")), "FFmpeg vorhanden", shutil.which("ffmpeg") or "nicht gefunden"))

    preset_path = BASE / "botconfig" / "stream_presets.json"
    try:
        presets = json.loads(preset_path.read_text(encoding="utf-8"))
        checks.append(result(set(presets) == {"1", "2", "3", "4", "5"}, "Fünf Presets geladen"))
        checks.append(result(presets["5"].get("type") == "local_autodj", "Preset 5 ist Local AutoDJ"))
    except Exception as exc:
        checks.append(result(False, "Preset-Datei lesbar", str(exc)))

    for directory in ("db", "runtime", "music", "botconfig"):
        path = BASE / directory
        try:
            path.mkdir(parents=True, exist_ok=True)
            probe = path / ".write-test"
            probe.write_text("ok", encoding="utf-8")
            probe.unlink()
            checks.append(result(True, f"Ordner beschreibbar: {directory}"))
        except Exception as exc:
            checks.append(result(False, f"Ordner beschreibbar: {directory}", str(exc)))

    token = os.getenv("DISCORD_TOKEN", "").strip()
    checks.append(result(bool(token and "PASTE_" not in token), "DISCORD_TOKEN gesetzt", "Wert wird nicht ausgegeben"))
    worker_token = os.getenv("RADIOBOTAI_WORKER_TOKEN", "").strip()
    checks.append(result(bool(worker_token), "RADIOBOTAI_WORKER_TOKEN gesetzt", "Wert wird nicht ausgegeben"))

    print("\nSelftest beendet.")
    return 0 if all(checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
