# Kubernetes manifests (prod skeleton)

Phase 2.2 deliverable — **not production-ready**. Replace image tags, resources,
network policies, and secret refs before any client data.

Suggested layout (add as services mature):

| Manifest | Role |
|----------|------|
| `namespace.yaml` | `ala` namespace |
| `postgres.yaml` | StatefulSet or managed Cloud SQL / Azure PG |
| `neo4j.yaml` | Graph for Evidence Matrix |
| `minio.yaml` / CSI | S3-compatible evidence store |
| `api-deployment.yaml` | FastAPI gateway |
| `networkpolicy.yaml` | Default deny + explicit allows |
| `externalsecret.yaml` | Vault / External Secrets Operator |

**Security:** private cluster, no public load balancer for matter APIs without auth,
encryption at rest, pod security standards restricted.
