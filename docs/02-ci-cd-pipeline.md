# The CI/CD Pipeline (GitHub Actions)

## Pipeline map

```
push / pull request
        |
        v
 1. Lint + unit tests      flake8, pytest                  (every push and PR)
        |
        v
 2. Build + integration    docker compose up, smoke test    (every push and PR)
        |
        v   (only on main)
 3. Publish image          push to ghcr.io (latest + sha)
        |
        v
 4. Deploy to staging      pull the published image, run it, smoke test
        |
        v
 5. Deploy to production   approval gate, deploy hook, health check
        |
        v
 6. Monitor                scheduled health checks every 30 minutes
```

## GitHub Actions vocabulary
| Term | Meaning in this repo |
|---|---|
| Workflow | A YAML file in `.github/workflows/` (`ci-cd.yml`, `monitor.yml`) |
| Trigger (`on:`) | What starts it: push, pull_request, schedule, manual |
| Job | A group of steps on one runner (`test`, `build`, `publish`...) |
| `needs:` | Makes a job wait for another, so stages run in order |
| Step | One command or reusable action |
| Runner | The fresh Ubuntu VM that runs the job |
| Action (`uses:`) | A reusable step such as `actions/checkout@v4` |
| Secret | Encrypted value (e.g. a deploy hook URL), hidden in logs |
| Variable | Plain configuration (e.g. `APP_URL`) |
| Environment | A named target (`staging`, `production`) with its own secrets and optional approvals |
| `GITHUB_TOKEN` | A temporary token GitHub gives each run, used to push to GHCR |

## Stage by stage

**1. Lint and test.** `flake8` checks style and obvious bugs, `pytest` runs the unit tests with a SQLite database. Fast (about a minute) and catches most mistakes.

**2. Build and integration test.** Builds the Docker image and starts the real stack (web + PostgreSQL) with Compose. `scripts/smoke_test.sh` waits for `/health`, writes a guestbook entry, reads it back and checks `/metrics`.

**3. Publish.** Only on `main`. Builds the image with `APP_VERSION` and `GIT_SHA` baked in and pushes it to GHCR as `latest` and `sha-xxxxxxx`.

**4. Deploy to staging.** Pulls the *published* image (not a fresh build), starts it with Compose, smoke tests it, and tears it down. This proves the exact artifact that will go to production works.

**5. Deploy to production.** Uses the `production` environment. If you add a required reviewer, the job waits for approval. If the `RENDER_DEPLOY_HOOK_URL` secret exists, it triggers a deploy; then a health check calls `APP_URL/health`.

## Environment management
- Config is in **environment variables**, never in code.
- `.env` is git-ignored; only `.env.example` is committed.
- In the pipeline, throwaway values are generated per run (`openssl rand`), so no real secret is stored in the repo.
- Real secrets (deploy hook) live in **Settings -> Environments -> production -> Secrets**.
- Different environments (`development`, `staging`, `production`) differ only by their variables.

## Pipeline best practices used
- `needs:` ordering so a failed test stops the build.
- `concurrency:` cancels outdated runs of the same branch.
- `permissions:` least privilege (read by default, `packages: write` only in the publish job).
- Dependency and Docker layer caching for speed.
- `if: always()` on log and teardown steps, so you get logs even when a step fails.
- Pin actions to a major version (`@v4`).

## Rollback
Every image is tagged with its commit SHA, so rolling back means redeploying an older tag, or `git revert` the bad commit and let the pipeline redeploy.
