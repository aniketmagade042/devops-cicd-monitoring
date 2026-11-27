# Monitoring and Observability (basics)

## Why monitor?
Deploying is not the finish line. You need to know quickly whether the release works and how it behaves.

## The three pillars
| Pillar | Question it answers | In this project |
|---|---|---|
| **Logs** | What happened? | One line per request, written to stdout |
| **Metrics** | How much / how often? | `/metrics` counters and uptime |
| **Health checks** | Is it alive? | `/health` (also checks the database) |

(A fourth pillar, traces, follows one request across services and is not needed for a single service.)

## Logs
The app writes structured lines to stdout:
```
2026-11-26 10:11:04 INFO guestbook: request method=POST endpoint=sign status=302 duration_ms=4.2
```
- **Why stdout?** Docker and cloud platforms collect it. View it with `docker compose logs -f web`.
- Log **events**, never passwords, tokens or personal data (the app logs name *length*, not the name).
- Log levels: DEBUG (details), INFO (normal events), WARNING (odd but fine), ERROR (something failed).
- Health and metrics requests log at DEBUG so they don't flood the output.

## Metrics
`GET /metrics` returns Prometheus text format:
```
guestbook_requests_total{endpoint="index",method="GET",status="200"} 12
guestbook_uptime_seconds 340
guestbook_build_info{version="17",git_sha="abc1234..."} 1
```
- A **counter** only goes up (requests). A **gauge** goes up and down (uptime, memory).
- Counters are per Gunicorn worker. With 2 workers each one reports its own totals; a real setup scrapes and sums them with Prometheus.
- Useful derived numbers: request rate, error rate (5xx / total), latency.

## Health checks
- `/health` returns 200 `{"db":"ok"}` or 503 `{"db":"down"}`.
- Used by: the Docker `HEALTHCHECK`, Compose (`depends_on: service_healthy`), the CI smoke test, and the uptime monitor.
- `/version` shows which build is live, which makes "did my deploy actually go out?" a one-second check.

## Alerting
`.github/workflows/monitor.yml` runs every 30 minutes, calls `APP_URL/health` up to 3 times, and **fails the workflow** if it is down. GitHub emails you about failed runs, which acts as a basic alert.

Limits to know about: scheduled workflows can run late, and GitHub disables them after 60 days of repository inactivity on public repos. Real teams use a dedicated tool (UptimeRobot, Grafana, Datadog, CloudWatch).

## Debugging a failed deploy
1. Open the failed run in the **Actions** tab and read the red step.
2. Check the container logs step (`docker compose logs web`).
3. Reproduce locally: `docker compose up -d --build`.
4. Call `/health` and `/version` to see what is running.
5. Fix, push, and let the pipeline run again.
