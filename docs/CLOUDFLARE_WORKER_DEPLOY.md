# Cloudflare Worker Deploy

## Ziel

Der Cloudflare Worker `666myidjshoutcaststream` soll nur den Ordner `worker/` deployen.

## Dashboard-Einstellung

```text
Repo: xfraggelpower666x/666-Radio-Core-Discord-Bot
Branch: Codex
Root directory / Stammverzeichnis: worker
Build command / Build-Befehl: leer
Deploy command / Bereitstellungsbefehl: npx wrangler deploy
```

## Custom Domain

```text
666myidjshoutcaststream.666soundsdesign-broadcaster.com
```

## Nach Deploy prüfen

```text
/health
/presets
/preset/1
/nowplaying
```

## Wichtig

Wenn `Root directory` leer bleibt, kann Cloudflare versuchen, den Discord-Bot aus dem Repo-Root als Worker zu deployen. Das ist falsch. Der Worker liegt absichtlich in `worker/`.
