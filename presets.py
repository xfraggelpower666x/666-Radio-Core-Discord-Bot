from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_PRESET_FILE = BASE_DIR / "botconfig" / "stream_presets.json"


@dataclass(frozen=True)
class StreamPreset:
    preset_id: str
    name: str
    type: str
    url: str
    description: str

    @property
    def playable(self) -> bool:
        return self.type == "audio_stream" and bool(self.url)


class PresetRegistry:
    def __init__(self, path: Path = DEFAULT_PRESET_FILE):
        self.path = path
        self._presets: Dict[str, StreamPreset] = {}
        self.reload()

    def reload(self) -> None:
        with self.path.open("r", encoding="utf-8") as handle:
            raw = json.load(handle)
        if not isinstance(raw, dict) or not raw:
            raise RuntimeError("stream_presets.json enthält keine Presets.")
        parsed: Dict[str, StreamPreset] = {}
        for preset_id, item in raw.items():
            if not isinstance(item, dict):
                raise RuntimeError(f"Preset {preset_id!r} ist ungültig.")
            preset_type = str(item.get("type", "audio_stream")).strip()
            if preset_type not in {"audio_stream", "external_link", "local_autodj"}:
                raise RuntimeError(f"Preset {preset_id!r}: unbekannter Typ {preset_type!r}.")
            parsed[str(preset_id)] = StreamPreset(
                preset_id=str(preset_id),
                name=str(item.get("name") or preset_id),
                type=preset_type,
                url=str(item.get("url") or "").strip(),
                description=str(item.get("description") or "").strip(),
            )
        self._presets = parsed

    def get(self, preset_id: str) -> StreamPreset:
        try:
            return self._presets[preset_id]
        except KeyError as exc:
            raise ValueError(f"Unbekanntes Preset: {preset_id}") from exc

    def all(self) -> Iterable[StreamPreset]:
        return self._presets.values()

    def ids(self) -> list[str]:
        return list(self._presets.keys())

    def audio_presets(self) -> list[StreamPreset]:
        return [preset for preset in self._presets.values() if preset.playable]

    def first_audio_id(self) -> str | None:
        audio = self.audio_presets()
        return audio[0].preset_id if audio else None
