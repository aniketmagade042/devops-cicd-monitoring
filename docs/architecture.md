# Architecture

```mermaid
flowchart LR
    Dev[Developer] -->|git push / PR| GH[GitHub repo]
    GH --> CI

    subgraph CI[GitHub Actions: CI/CD pipeline]
        direction LR
        T[1. Lint + pytest] --> B[2. Docker build + smoke test]
        B --> P[3. Publish image to GHCR]
        P --> S[4. Staging deploy + smoke test]
        S --> D[5. Production deploy]
    end

    P --> GHCR[(GitHub Container Registry)]
    D -->|deploy hook| R[Render web service: Docker, Gunicorn, Flask]
    R <-->|SSL| N[(Neon PostgreSQL)]
    User[Users] -->|HTTPS| R

    M[Uptime monitor: scheduled every 30 min] -->|GET /health, /version| R
    R -.->|/metrics, request logs| O[Observability]
```

| Component | Role |
|---|---|
| GitHub Actions | Lint, test, build, publish, deploy |
| GHCR | Stores versioned Docker images (`latest` + commit SHA) |
| Render | Runs the container in production |
| Neon | Managed PostgreSQL database |
| Uptime monitor | Scheduled workflow that checks `/health` and `/version` |
