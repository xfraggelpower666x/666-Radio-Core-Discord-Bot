# Deploy Attempt 2026-06-03

## Scope

Command requested: `go`

Actions attempted from repo branch `Codex`:

- Worker syntax check from `worker/`
- Cloudflare Worker deploy using documented command `npx wrangler deploy`
- Discord command registration only if `discord-bot/.env` exists
- Live smoke test against known Worker URLs

## Results

| Check | Result | Notes |
|---|---|---|
| Git status | PASS | Local branch was clean before deploy attempt. |
| Worker syntax | PASS | `npm run check` succeeded in `worker/`. |
| Cloudflare deploy | BLOCKED | Wrangler requires `CLOUDFLARE_API_TOKEN` in non-interactive mode. |
| Discord `.env` | MISSING | `discord-bot/.env` does not exist; command registration skipped. |
| Workers.dev `/health` | HTTP 200, NOT v1.3.0 | Response body: `Hello World!` |
| Custom domain `/health` | HTTP 200, NOT v1.3.0 | Response body: `Hello World!` |

## Finding

The repository is prepared for v1.3.0, but the live Cloudflare Worker currently does not appear to be running the committed v1.3.0 Worker code. It still returns `Hello World!` for `/health`.

## Required External Action

One of these is required:

- Set `CLOUDFLARE_API_TOKEN` in the deploy environment and run `cd worker && npx wrangler deploy`.
- Trigger Cloudflare Git deploy from the dashboard with Root Directory set to `worker`.

Do not put the Cloudflare token in the repository.
