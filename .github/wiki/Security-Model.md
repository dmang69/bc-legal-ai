# Security Model

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────┐
│                    Authentication Layer                    │
│  ┌─────────────────────────────────────────────────────┐ │
│  │  Bearer Token (API)  |  HttpOnly Cookie (Web PWA)   │ │
│  └─────────────────────┬───────────────────────────────┘ │
│                        │                                  │
│  ┌─────────────────────▼───────────────────────────────┐ │
│  │              Authorization Layer                      │ │
│  │  1. Validate organization membership                  │ │
│  │  2. Check ethical wall / revocation (deny-first)      │ │
│  │  3. Apply role-based access (owner/admin/member)      │ │
│  │  4. Check matter membership + access level            │ │
│  └─────────────────────┬───────────────────────────────┘ │
│                        │                                  │
│  ┌─────────────────────▼───────────────────────────────┐ │
│  │                 Audit Layer                           │ │
│  │  - Every action recorded in append-only hash chain   │ │
│  │  - Tamper-evident: chain breaks detectable           │ │
│  │  - PostgreSQL advisory locks prevent race conditions │ │
│  └─────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

## Key Security Properties

### Authentication
- **API**: Bearer tokens (SHA-256 hashed in DB)
- **Web**: HttpOnly, Secure, SameSite=Strict cookies
- **Session**: 12-hour TTL, server-side revocation
- **Password**: Argon2id with per-user salt, minimum 10 chars

### Authorization (Deny-First)
1. Organization membership verified
2. Ethical wall or revocation checked FIRST
3. Deny regardless of role if explicit denial exists
4. Role-based access applied only after denial check

### Audit Integrity
- SHA-256 hash chain prevents undetected tampering
- PostgreSQL advisory lock serializes concurrent appends
- Verification endpoint checks full chain integrity
- Optional external checkpoint anchoring

### Data Protection
| Layer | Mechanism |
|-------|-----------|
| In-transit | TLS 1.3 (min) |
| At-rest (DB) | Transparent Data Encryption |
| At-rest (Blob) | Server-side encryption (AES-256) |
| Secrets | Vault / External Secrets Operator |

## Rate Limiting
- Redis-backed token bucket (100 req/min per user)
- Burst allowance: 50 requests
- Exponential backoff after rate limit exceeded

## Incident Response
1. Automated alert via PagerDuty/Slack
2. Session mass revocation capability
3. Audit chain forensic analysis
4. Backup restoration (RPO: 1 hour, RTO: 4 hours)
5. Post-mortem within 72 hours
