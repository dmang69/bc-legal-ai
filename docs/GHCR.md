# GitHub Container Registry (GHCR)

**Image:** `ghcr.io/dmang69/bc-legal-ai`

Primary distribution channel for end users and operators. No clone/build required.

## One-command run

```bash
docker run --rm -p 8000:8000 \
  -e APP_MODE=development \
  ghcr.io/dmang69/bc-legal-ai:latest
```

Open:

- API docs: http://127.0.0.1:8000/docs  
- Health: http://127.0.0.1:8000/health  

Smoke:

```bash
# from a checkout of this repo (optional)
python scripts/production_smoke.py --base http://127.0.0.1:8000
```

## Tags

| Tag | Meaning |
|-----|---------|
| `latest` | Latest **version tag** release (e.g. after `v1.0.0`) |
| `1.0.0` / `1.0` / `1` | Semver pins from git tags |
| `edge` | Rolling build from `main` |
| `sha-xxxxxxx` | Immutable commit pin |

```bash
docker pull ghcr.io/dmang69/bc-legal-ai:1.0.0
docker pull ghcr.io/dmang69/bc-legal-ai:edge
```

## Compose (pull-only)

```bash
docker compose -f docker-compose.ghcr.yml up
# pin: IMAGE_TAG=1.0.0 docker compose -f docker-compose.ghcr.yml up
```

## Production-ish run

```bash
docker run -d --name bc-legal-ai -p 8000:8000 \
  -e APP_MODE=production \
  -e ALA_POSTGRES_URL='postgresql://user:pass@host:5432/ala' \
  -e CORS_ORIGINS='https://app.example.com' \
  -e ALA_COOKIE_SECURE=1 \
  --restart unless-stopped \
  ghcr.io/dmang69/bc-legal-ai:latest
```

Put TLS in front (Caddy/nginx/cloud LB). See [`CLOUD_DEPLOY.md`](CLOUD_DEPLOY.md).

## How images are published (maintainers)

Workflow: [`.github/workflows/publish-ghcr.yml`](../.github/workflows/publish-ghcr.yml)

| Event | Tags pushed |
|-------|-------------|
| Push to `main` | `edge`, `sha-…` |
| Git tag `v*` | `latest`, semver, `sha-…` |
| Actions → **Publish GHCR** → Run workflow | same + optional extra tag |

Pipeline always **smokes the image** (`production_smoke.py`) before push.

### First-time package visibility (one-time GitHub UI)

1. After the first successful publish, open  
   `https://github.com/users/dmang69/packages/container/bc-legal-ai/settings`  
   (or org equivalent under the repo **Packages** sidebar).  
2. Set **Visibility → Public** if you want anonymous `docker pull`.  
3. Optional: link package to the `bc-legal-ai` repository.

Private packages require:

```bash
echo $CR_PAT | docker login ghcr.io -u USERNAME --password-stdin
```

(`read:packages` scope; `write:packages` only for publishers.)

## Kubernetes

```yaml
image: ghcr.io/dmang69/bc-legal-ai:1.0.0
```

Update `infra/k8s/api-deployment.yaml` and Helm values accordingly.

## What is in the image

- FastAPI API (`backend.api.main:app`)
- Portable SQLite default (volume optional at `/app/data`)
- Postgres client libraries for `ALA_POSTGRES_URL`
- Non-root user (`appuser`)
- **No** secrets baked in; **no** platform-ui static (serve UI separately or use HF demo)

## Legal / safety

Not a lawyer. Not legal advice. Public demos and casual `docker run` are for **synthetic / supervised** evaluation. Do not load confidential client files into an unsecured host.
