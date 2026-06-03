# Codex Next Steps

1. Verify new GitHub Actions Radio Core CI run on branch Codex.
2. Verify Cloudflare Root Directory = worker.
3. Configure discord-bot/.env outside Git.
4. Register slash commands with real Discord env.
5. Start Bot on 24/7 Node host.
6. Configure RADIO_LOG_CHANNEL_ID if track/health events should be posted to Discord.
7. Test /play, /pause, /resume, /stop, /volume, /radio panel/status.
8. Verify ICY StreamTitle appears in /radio status and track-change log posts.
9. Verify stream health transitions with a real SHOUTcast/Icecast URL.
10. Capture SonicPanel Skip/Jingle endpoints without secrets.
11. Deploy Worker and test /health, /presets, /nowplaying.
12. Provide `CLOUDFLARE_API_TOKEN` in the deploy environment or trigger Cloudflare Git deploy from the dashboard; current live `/health` returns `Hello World!`.
