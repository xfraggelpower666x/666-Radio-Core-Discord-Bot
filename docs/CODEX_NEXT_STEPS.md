# Codex Next Steps

1. Provide `CLOUDFLARE_API_TOKEN` in the deploy environment or trigger Cloudflare Git deploy from the dashboard; current live `/health` returns `Hello World!`.
2. Verify Cloudflare Root Directory = worker.
3. Deploy Worker and test /health, /presets, /nowplaying.
4. Configure discord-bot/.env outside Git.
5. Register slash commands with real Discord env.
6. Start Bot on 24/7 Node host.
7. Configure RADIO_LOG_CHANNEL_ID if track/health events should be posted to Discord.
8. Test /play, /pause, /resume, /stop, /volume, /radio panel/status.
9. Verify ICY StreamTitle appears in /radio status and track-change log posts.
10. Verify stream health transitions with a real SHOUTcast/Icecast URL.
11. Capture SonicPanel Skip/Jingle endpoints without secrets.
