"""666 RadioBotAI preset registry for add-on commands."""

from __future__ import annotations


PRESETS: dict[str, dict[str, str]] = {
    "1": {
        "label": "Main WebRadio",
        "description": "Primaerer 666SOUNDsDESIGn WebRadio Stream.",
        "worker_path": "/preset/1",
    },
    "2": {
        "label": "Fallback WebRadio",
        "description": "Fallback Stream / Backup-Ausgabe.",
        "worker_path": "/preset/2",
    },
    "3": {
        "label": "AutoDJ Rotation",
        "description": "Vorbereiteter AutoDJ Preset-Platzhalter.",
        "worker_path": "/preset/3",
    },
    "4": {
        "label": "Live DJ",
        "description": "Vorbereiteter Live-DJ Preset-Platzhalter.",
        "worker_path": "/preset/4",
    },
    "5": {
        "label": "Maintenance",
        "description": "Wartungs-/Test-Preset-Platzhalter.",
        "worker_path": "/preset/5",
    },
}


def get_presets() -> dict[str, dict[str, str]]:
    return dict(PRESETS)


def get_preset(name: str) -> dict[str, str] | None:
    key = str(name or "").strip().lower()
    if key in PRESETS:
        return dict(PRESETS[key])

    for preset_key, preset in PRESETS.items():
        if key == preset.get("label", "").lower():
            return {"key": preset_key, **preset}
    return None

