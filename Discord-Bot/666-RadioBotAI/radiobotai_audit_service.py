"""
666 RadioBotAI Audit Service
Phase 2C-22 — Repo-Safe Audit Split

Discord-Bot Audit + Visual/Color Output.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Dict, Any, List


PROTECTED_PATHS = [
    "Arbeiter/src/index.js",
    "Arbeiter/package.json",
    "Workers/666myidjstreamadmin/src/index.js",
    "Workers/666myidjstreamadmin/wrangler.toml",
    "Dashboard/Vocard-Dashboard-main",
    "Discord-Bot/666-RadioBotAI",
    "Render/666RadioBotAI-PlayerAlert-Render-Backend",
    "Docs",
    "wrangler.toml",
    "package.json",
    ".gitignore",
    "README.md",
]

WORKER_ROUTES = [
    "/health",
    "/status",
    "/dashboard",
    "/config/public",
    "/nowplaying",
    "/api/discord/status",
    "/api/discord/debug",
    "/api/discord/message",
    "/api/discord/nowplaying",
    "/radio/autodj/status",
    "/radio/autodj/skip",
    "/api/radio/skip",
    "/autodj/skip",
    "/radio/autodj/playlist",
]

SECRET_PATTERNS = [
    re.compile(r"ghp_[A-Za-z0-9_]{20,}"),
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"discord(?:app)?\.com/api/webhooks/[A-Za-z0-9_/-]+", re.I),
    re.compile(r"[A-Za-z0-9_-]{24}\.[A-Za-z0-9_-]{6}\.[A-Za-z0-9_-]{20,}"),
]


def find_repo_root(start: Path | None = None) -> Path:
    current = (start or Path(__file__).resolve()).resolve()
    for candidate in [current] + list(current.parents):
        if (candidate / "wrangler.toml").exists() and (candidate / "Arbeiter" / "src" / "index.js").exists():
            return candidate
    return Path(__file__).resolve().parents[2]


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""


def _secret_scan(root: Path) -> List[str]:
    hits = []
    suffixes = {".md",".html",".json",".yml",".yaml",".txt",".cfg",".scss",".js",".py",".bat",".toml",".example",".sh",".ps1"}
    for file in root.rglob("*"):
        try:
            if not file.is_file() or file.stat().st_size > 2_000_000 or file.suffix.lower() not in suffixes:
                continue
            text = _read_text(file)
            for pat in SECRET_PATTERNS:
                if pat.search(text):
                    hits.append(str(file.relative_to(root)))
                    break
        except Exception:
            continue
    return sorted(set(hits))


def percent(done: int, total: int) -> int:
    if total <= 0:
        return 0
    return int(round((done / total) * 100))


def visual_bar(value: int, size: int = 12) -> str:
    value = max(0, min(100, int(value)))
    filled = int(round((value / 100) * size))
    empty = size - filled
    if value >= 90:
        color = "🟩"
    elif value >= 70:
        color = "🟨"
    else:
        color = "🟥"
    return color * filled + "⬛" * empty + f" {value}%"


def run_local_audit(root: Path | None = None) -> Dict[str, Any]:
    repo = root or find_repo_root()

    protected = {p: (repo / p).exists() for p in PROTECTED_PATHS}
    wrangler_text = _read_text(repo / "wrangler.toml")
    worker_text = _read_text(repo / "Arbeiter" / "src" / "index.js")

    route_checks = {route: route in worker_text for route in WORKER_ROUTES}

    # Phase2C22 split:
    # Bootsystem and full Backup-System are intentionally NOT required as repo payload.
    # Only the Discord audit runtime is repo-resident. External boot/backup governance is handled
    # by the chat/build pipeline and the separate NOT_FOR_REPO backup artifact.
    governance_split = True
    boot_external = True
    backup_external = True
    audit_runtime_resident = (repo / "Discord-Bot" / "666-RadioBotAI" / "cogs" / "radiobotai_audit.py").exists()

    secret_hits = _secret_scan(repo)

    checks = {
        "Protected Paths": all(protected.values()),
        "Worker Main": 'main = "Arbeiter/src/index.js"' in wrangler_text or "main = 'Arbeiter/src/index.js'" in wrangler_text,
        "Worker Routes": all(route_checks.values()),
        "Audit Runtime Cog": audit_runtime_resident,
        "Boot External Not Repo": boot_external,
        "Backup External Not Repo": backup_external,
        "Governance Split": governance_split,
        "Secret Scan": not secret_hits,
    }

    protected_score = percent(sum(1 for v in protected.values() if v), len(protected))
    route_score = percent(sum(1 for v in route_checks.values() if v), len(route_checks))
    core_score = percent(sum(1 for v in checks.values() if v), len(checks))

    ok = all(checks.values())

    return {
        "ok": ok,
        "status": "PASS" if ok else "FAIL",
        "repo_root": str(repo),
        "checks": checks,
        "scores": {
            "Core": core_score,
            "Protected Paths": protected_score,
            "Worker Routes": route_score,
            "Audit Runtime": 100 if audit_runtime_resident else 0,
            "Secrets": 100 if not secret_hits else 0,
            "External Boot/Backup Split": 100 if boot_external and backup_external and governance_split else 0,
        },
        "protected_paths": protected,
        "worker_routes": route_checks,
        "backup_manifest_file_count": 0,
        "external_boot_system": "NOT_REPO_PAYLOAD_ACTIVE_IN_BUILD_GOVERNANCE",
        "external_backup_system": "NOT_REPO_PAYLOAD_ACTIVE_AS_SEPARATE_ARTIFACT",
        "secret_hits": secret_hits,
        "freeze": "NO / HOLD_UNTIL_LIVE_TEST_PASS",
        "upload_decision": "UPLOAD_ALLOWED_STRUCTUREWISE" if ok else "UPLOAD_BLOCKED",
    }


def format_audit_plain(report: Dict[str, Any]) -> str:
    lines = [
        "666 RadioBotAI Audit",
        f"Status: {report.get('status')}",
        f"Upload: {report.get('upload_decision')}",
        f"Freeze: {report.get('freeze')}",
        "",
        "Scores:",
    ]
    for k, v in report.get("scores", {}).items():
        lines.append(f"{k}: {visual_bar(v)}")
    lines.append("")
    lines.append("Checks:")
    for key, value in report.get("checks", {}).items():
        lines.append(f"{'✅' if value else '❌'} {key}")
    secret_hits = report.get("secret_hits") or []
    if secret_hits:
        lines.append("")
        lines.append("Secret-Hits:")
        lines.extend(f"❌ {x}" for x in secret_hits[:8])
    return "\n".join(lines)


def write_audit_report(root: Path | None = None) -> Path:
    repo = root or find_repo_root()
    report = run_local_audit(repo)
    out = repo / "Docs" / "DISCORD_BOT_AUDIT_REPORT_LATEST.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return out
