# DevOps, CI/CD and Monitoring Lab

A small Flask + PostgreSQL service with a full GitHub Actions pipeline:

**GitHub -> Build -> Test -> Docker -> Deploy -> Monitor**

[![CI/CD](https://github.com/aniketmagade042/devops-cicd-monitoring/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/aniketmagade042/devops-cicd-monitoring/actions/workflows/ci-cd.yml)
**Live demo:** https://devops-guestbook.onrender.com (free tier, the first load can take about a minute)
Architecture: [docs/architecture.md](docs/architecture.md)
## Pipeline

```
push / pull request
   |
   v
1. Lint + unit tests (flake8, pytest)
   |
   v
2. Build Docker image + integration test (Compose, smoke test)
   |
   v   only on main
3. Publish image to GitHub Container Registry (latest + sha)
   |
   v
4. Deploy to staging (pull published image, smoke test)
   |
   v
5. Deploy to production (approval gate, deploy hook, health check)
   |
   v
6. Monitor (scheduled health checks, /metrics, logs)
```

| Module objective | Where it is in this repo |
|---|---|
| DevOps culture, Git/GitHub workflow | `docs/01-devops-and-git-workflow.md`, PR template, branch + PR flow |
| Automated testing | `tests/`, `pytest` and `flake8` in `.github/workflows/ci-cd.yml` |
| Build automation | Docker build in the `build` and `publish` jobs |
| Deployment automation | `deploy-staging` and `deploy-production` jobs |
| Environment management | GitHub Environments, generated per-run secrets, `.env.example` |
| Monitoring and logs | `/health`, `/version`, `/metrics`, request logs, `.github/workflows/monitor.yml` |

## Repo structure

```
app/                         Flask app (health, version, metrics endpoints)
tests/                       unit tests
scripts/smoke_test.sh        post-deploy smoke test
.github/workflows/ci-cd.yml  build, test, publish, deploy pipeline
.github/workflows/monitor.yml scheduled uptime check
Dockerfile, docker-compose.yml
docs/                        learning notes
screenshots/                 evidence
```

## Run locally

```bash
pip install -r requirements.txt -r requirements-dev.txt
flake8 app tests
pytest -v
```

Or run the full stack:

```bash
cp .env.example .env      # then set SECRET_KEY and POSTGRES_PASSWORD
docker compose up -d --build
bash scripts/smoke_test.sh http://localhost:8000
```

## Observability endpoints

| Endpoint | Purpose |
|---|---|
| `/health` | Liveness and database check |
| `/version` | Running build number and commit SHA |
| `/metrics` | Request counters in Prometheus text format |

Logs: `docker compose logs -f web` shows one line per request (method, endpoint, status, duration).

## GitHub setup used

1. Repo secrets and variables: variable `APP_URL` (the live app URL, for health checks), optional secret `RENDER_DEPLOY_HOOK_URL` on the `production` environment.
2. Environments: `staging` and `production` (optional required reviewer on production).
3. Branch protection on `main`: require the `1. Lint and unit tests` and `2. Build image and integration test` checks before merging.

## Evidence 

| What | File |
|---|---|
| Git push from the Codespace | `screenshots/00-git-push.png` |
| Pipeline run list (run #1 green) | `screenshots/01-pipeline-run.png` |
| Pipeline run with all jobs green | `screenshots/01-pipeline-success.png` |
| Lint and test job logs | `screenshots/02-test-job.png` |
| A pull request with a failing check (then fixed) | `screenshots/03-failed-then-fixed-pr.png` |
| Image published in GitHub Packages (GHCR) | `screenshots/04-ghcr-package.png` |
| Staging deploy and smoke test logs | `screenshots/05-staging-deploy.png` |
| Staging and production deployments | `screenshots/06-environments.png` |
| Uptime monitor health check log | `screenshots/07-monitor-run.png` |
| Uptime monitor runs | `screenshots/07b-monitor-runs.png` |
| `/version` and `/metrics` output | `screenshots/08-version-metrics.png` |
| Container logs showing request lines | `screenshots/09-container-logs.png` |
| Production pipeline, all jobs green (push) | `screenshots/12-prod-pipeline-success.png` |
| Render deploy triggered by the pipeline | `screenshots/13-render-deploy-hook.png` |
| Live app with saved messages | `screenshots/14-live-site.png` |
## Challenges and fixes

- **Screenshots not showing in the commit:** I ran `git add .` from inside the `app/` folder, so the `screenshots/` folder was never staged and the push said "Everything up-to-date". I fixed it by running `git add -A` from the repo root.
- **Doubled file extensions (`.png.png`):** Windows added a second extension when I saved screenshots, so the README links were broken. I renamed the files with `git mv` and committed.
- **Proving the lint gate works:** I opened a PR with a deliberate unused import. The `Lint and unit tests` job failed and the build, publish and deploy jobs were skipped. After I removed the line, all checks passed. This confirms bad code can't reach staging or production.



## Author

Aniket Magade | [LinkedIn](https://www.linkedin.com/in/aniket-magade-959601448/)
