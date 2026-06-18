"""
666 RadioBotAI AI Client
Phase 2C-6

Ziel:
- AI-Addon als eigene RadioBotAI-Brücke vorbereiten.
- Keine API Keys im Code, Chat, Dashboard oder Repo.
- Bot fragt den Worker; Worker hält später AI Provider Secret serverseitig.
"""

import os
import aiohttp


class RadioBotAIAIClient:
    def __init__(self):
        self.worker_url = os.getenv("RADIOBOTAI_WORKER_URL", "https://666radiobotai.666soundsdesign-broadcaster.com").rstrip("/")
        self.admin_token = os.getenv("RADIOBOTAI_ADMIN_TOKEN", "")

    async def ask(self, prompt: str, mode: str = "radio_assistant"):
        headers = {"content-type": "application/json"}
        if self.admin_token:
            headers["x-radiobotai-gate"] = self.admin_token
            headers["x-admin-token"] = self.admin_token
            headers["x-discord-gate-code"] = self.admin_token
            headers["authorization"] = f"Bearer {self.admin_token}"

        payload = {
            "prompt": prompt,
            "mode": mode,
            "source": "discord_bot"
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(f"{self.worker_url}/api/ai/ask", json=payload, headers=headers, timeout=30) as res:
                try:
                    data = await res.json()
                except Exception:
                    data = {"ok": False, "error": "invalid_json", "status": res.status}
                return res.status, data


def ai_status_config():
    return {
        "worker_url": os.getenv("RADIOBOTAI_WORKER_URL", "https://666radiobotai.666soundsdesign-broadcaster.com"),
        "admin_token_configured": bool(os.getenv("RADIOBOTAI_ADMIN_TOKEN")),
        "mode": "worker_bridge_only_no_secret_in_bot",
    }
