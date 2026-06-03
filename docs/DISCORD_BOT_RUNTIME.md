# Discord Bot Runtime

## Ziel

Der Discord-Bot läuft separat als echter Node.js-Prozess.

## Warum nicht Cloudflare Worker?

Der Bot benötigt eine dauerhafte Discord-Gateway-Verbindung, Voice-Channel-Verbindung und Audio-Playback über FFmpeg/Opus. Das gehört in eine Node.js-Runtime, nicht in den normalen Cloudflare Worker.

## Start

```bash
cd discord-bot
cp .env.example .env
npm install
npm run register
npm start
```

## Windows

```powershell
cd discord-bot
.\start-666RadioCoreDJ.ps1 -Install
.\start-666RadioCoreDJ.ps1 -RegisterCommands
.\start-666RadioCoreDJ.ps1 -StartBot
```

## Befehle

```text
/play
/play preset:1
/pause
/resume
/stop
/volume
/volume level:80
/volume default:true
/radio panel
/radio status
/radio skip
/radio jingle name:...
```
