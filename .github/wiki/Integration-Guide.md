# Integration Guide

## BC Laws Integration

The system integrates with BC Laws for statute and regulation retrieval.

```python
from knowledgebase.source_registry import SourceRegistry

reg = SourceRegistry()
sources = reg.sources  # List of verified source definitions
```

## External Services

### Email / Notification (SMTP)

Configure via environment:
```
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=notifications@ala.example.com
SMTP_PASSWORD=***
```

### Document Storage (MinIO/S3)

Evidence files are stored in MinIO with:
- Immutable content-addressed storage
- Server-side encryption (SSE-S3)
- Pre-signed URLs for controlled access
- Automatic bucket lifecycle policies

### Queue / Workers (Redis)

For durable background job processing:
- Redis Streams for reliable message delivery
- Consumer groups for worker scaling
- Dead-letter queue for failed jobs
- Exponential backoff retry

## GitLab CI Integration (Project ID: 84788875)

### Variables to Configure

| Variable | Description |
|----------|-------------|
| `CI_REGISTRY_PASSWORD` | GitLab container registry password |
| `ALA_TEST_POSTGRES_URL` | Test PostgreSQL connection string |
| `SONAR_TOKEN` | SonarQube token for code quality |
| `KUBECONFIG` | Base64-encoded kubeconfig for deployment |

### Pipeline Stages

1. **Lint** — Ruff formatting and linting
2. **Test** — SQLite and PostgreSQL test suites
3. **Security** — Bandit, Safety, Dependency scanning
4. **Build** — Docker image build and SBOM generation
5. **Deploy** — Helm deployment to staging/production

## GitHub Actions

### Required Secrets

| Secret | Description |
|--------|-------------|
| `DOCKER_USERNAME` | Container registry username |
| `DOCKER_PASSWORD` | Container registry token |
| `CODECOV_TOKEN` | Codecov upload token |
| `SONAR_TOKEN` | SonarQube analysis token |

### Available Workflows

| Workflow | Trigger | Description |
|----------|---------|-------------|
| `ci.yml` | Push/PR to main/develop | Lint, test, security scan, Docker build |
| `release.yml` | Tag v* | Build image, generate SBOM, create release |

## Webhook Integrations

| Service | Endpoint | Purpose |
|---------|----------|---------|
| Slack | `#ala-deploy` | Deployment notifications |
| PagerDuty | API integration | Incident alerts |
| Datadog | API key | Monitoring and observability |
| Sentry | DSN | Error tracking |

## Monitoring Stack

- **Prometheus** — Metrics collection
- **Grafana** — Dashboards and alerting
- **Loki** — Log aggregation
- **Tempo** — Distributed tracing

## Security Integrations

- **Trivy** — Container vulnerability scanning
- **SonarQube** — Code quality and security analysis
- **Dependency-Check** — OWASP dependency scanning
- **ClamAV** — Malware scanning for uploaded evidence
