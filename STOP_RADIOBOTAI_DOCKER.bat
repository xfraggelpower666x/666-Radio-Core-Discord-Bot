@echo off
setlocal
cd /d "%~dp0"

if not exist .env (
  echo [666 RadioBotAI] .env fehlt.
  echo Kopiere .env.example nach .env und trage DISCORD_TOKEN, DISCORD_CLIENT_ID und RADIO_STREAM_URL ein.
  copy .env.example .env >nul
  echo .env wurde als Vorlage erstellt. Bitte bearbeiten und danach diese Datei erneut starten.
  pause
  exit /b 1
)

echo [666 RadioBotAI] Starte Docker Compose...
docker compose up -d --build

echo.
echo [666 RadioBotAI] Logs anzeigen mit: CHECK_RADIOBOTAI_LOGS.bat
pause
