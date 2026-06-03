# Rollback Plan

Last stable commit before v1.3 import: f0bdb29. Worker deploy rollback: Cloudflare dashboard or redeploy previous commit. Bot rollback: stop Node process, checkout known good commit, install dependencies, restart. Do not rollback by pointing Worker root to repo root.

