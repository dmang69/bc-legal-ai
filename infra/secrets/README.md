# Secrets / vault integration (scaffold)

**Never commit real secrets.** Use environment variables or a vault.

## Local dev

```bash
# example — do not use these values in production
export ALA_POSTGRES_URL=postgresql://ala:ala_dev_only_change_me@localhost:5432/ala
export ALA_NEO4J_URI=bolt://localhost:7687
export ALA_NEO4J_PASSWORD=ala_dev_only_change_me
export ALA_S3_ENDPOINT=http://localhost:9000
export ALA_S3_ACCESS_KEY=ala_minio
export ALA_S3_SECRET_KEY=ala_dev_only_change_me
export ALA_REDIS_URL=redis://localhost:6379/0
export ALA_RABBITMQ_URL=amqp://ala:ala_dev_only_change_me@localhost:5672/
```

## Production patterns

| Secret | Suggested store |
|--------|-----------------|
| DB credentials | HashiCorp Vault / cloud secret manager / K8s Secret |
| Object store keys | Vault + short-lived STS where possible |
| HF / model tokens | Private env only; never in public Space for client data |
| Encryption keys | KMS-backed |

## Placeholder files

- `vault-agent-config.hcl.example` — Vault Agent template
- `.env.example` — compose env template (no real passwords in git history of prod)
