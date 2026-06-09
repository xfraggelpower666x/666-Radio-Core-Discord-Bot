# Vocard Sovereign Merge Plan v1.1.0

## Entscheidung

Vocard ist die Dashboard-Hauptbasis. Der Worker-Minimalbuild v1.0.9 wird nicht als Zielsystem verwendet, sondern nur als Referenz für Worker-Endpunkte.

## Architektur

```text
Repo Root
├─ Arbeiter/                     Cloudflare Worker
├─ Dashboard/
│  ├─ Vocard-Dashboard-main/      erhaltene Vocard-Basis
│  └─ radiobotai-addon/           RadioBotAI-Erweiterung
├─ Discord-Bot/666-RadioBotAI/    Discord Voice Bot Core
├─ Installer/Vocard-Installer-main/
├─ Docs/
├─ wrangler.toml
├─ package.json
└─ .env.example
```

## Einbauprinzip

- Vocard Dashboard erhalten.
- RadioBotAI-Funktionen additiv ergänzen.
- Keine parallele Shooter-Logik bauen.
- Discord-Shooter nur über Worker/Backend/Secrets anbinden.
- Admin/Auth über geschützte Header/Auth-Worker vorbereiten.
