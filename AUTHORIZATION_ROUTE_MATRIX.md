# Authentication and Authorization Route Matrix

**Baseline:** 2026-07-23 repository state  
**Route sources:** `backend/api/main.py`, `backend/api/platform_routes.py`  
**Security rule:** Authentication identifies an actor; it does not authorize access to an organization, matter, resource, workflow transition, or privileged operation.

## Legend and policy

| Code | Meaning |
|---|---|
| Public | Deliberately unauthenticated; must expose no tenant data |
| Auth | Valid active session required |
| M:R / M:W / M:A | Matter read / write / admin authorization required |
| Obj→M | Resolve resource to organization/matter, then authorize that matter |
| Role | Additional application role/capability required |
| State | Resource/workflow state precondition required |
| Demo | Public-demo environment restriction applies |
| Service | Authorization currently occurs inside called service |
| GAP | Current implementation does not satisfy target policy |
| PARTIAL | Some control exists, but policy is incomplete or indirect |
| OK | Current implementation meets the documented route-level baseline |

### Global invariants

1. `CurrentUser`/valid session is required for every non-public route.
2. Ethical walls and revoked memberships deny before owner/admin role grants.
3. Owner/admin may receive implicit organization-level matter access only when no explicit denial exists; this does not replace resource state, privilege, or separation-of-duties checks.
4. Every matter path/body/query identifier requires M:R, M:W, or M:A.
5. Every opaque resource ID requires tenant-safe Obj→M resolution before existence or content is disclosed.
6. Mutations require M:W unless a stricter role/capability is specified.
7. Browser cookie mutations require CSRF; bearer API clients require an explicit non-cookie authentication profile.
8. Public routes receive rate limits, bounded inputs, generic errors, and no confidential persistence/logging.
9. Read-denial should avoid resource enumeration; use consistent 403/404 policy.
10. Database RLS is defense in depth, not a substitute for route/service authorization.

## A. Static, health, and design routes (`backend/api/main.py`)

| Method | Route | Current control | Target policy | Status / action |
|---|---|---|---|---|
| GET | `/` | Public static/redirect | Public; no tenant data | OK |
| GET | `/index.html` | Public static file | Public; containment check | OK |
| GET | `/styles.css` | Public static file | Public | OK |
| GET | `/app.js` | Public static file | Public; CSP/SRI/build integrity | OK baseline |
| GET | `/sw.js` | Public static file | Public; cache/update integrity | OK baseline |
| GET | `/manifest.webmanifest` | Public static file | Public | OK |
| GET | `/icons/{name}` | Public file selected from path | Public; resolved path must remain under icon root | PARTIAL — add explicit containment/traversal tests |
| GET | `/health` | Public; reports mode, DB backend, deployment state | Public shallow status only | PARTIAL — remove topology/detail from public response |
| GET | `/health/live` | Public liveness | Public `{status}` only | OK |
| GET | `/health/ready` | Public; may include raw exception text | Public shallow readiness; protected operator diagnostics | PARTIAL — suppress dependency exception details |
| GET | `/v1/design-locks` | Public static product/legal design metadata | Public | OK |

## B. Platform public and identity routes (`/v1/platform`)

| Method | Route | Current control | Target policy | Status / action |
|---|---|---|---|---|
| POST | `/workspace/analyze` | Public; public-text scan | Public synthetic-only, rate-limited, no confidential persistence/provider egress | PARTIAL — narrow DLP and abuse controls are insufficient for live data |
| GET | `/status` | Public; initializes DB and exposes backend/modules | Auth operator role, or public shallow status | GAP — must not trigger migrations or expose topology publicly |
| POST | `/auth/register` | Public; blocked in public demo | Invite/admin provisioning in production; rate limit and verified email | GAP for production open registration |
| POST | `/auth/login` | Public credential exchange | Public; rate limit, enumeration-safe errors, MFA/session issuance | PARTIAL — secure session/MFA controls pending |
| GET | `/auth/me` | `CurrentUser` | Auth | OK |
| POST | `/auth/logout` | Raw bearer token; revokes session | Auth session + CSRF for cookie client; revoke and clear cookie | PARTIAL — bearer revocation works; browser flow pending |
| GET | `/workspace/specialists` | Public static/service metadata | Public if metadata only; rate limited/cacheable | OK baseline |
| GET | `/workspace/modes` | Public static/service metadata | Public if metadata only | OK baseline |

## C. Platform workspace persistence and conversations

| Method | Route | Current control | Target policy | Status / action |
|---|---|---|---|---|
| POST | `/v1/platform/workspace/conversations` | Auth; Service checks optional matter | Auth + M:W when matter-bound | OK via Service; add route policy test |
| GET | `/v1/platform/workspace/conversations` | Auth; Service filters/checks matter | Auth + M:R when filtered; tenant-only general chats | OK via Service |
| GET | `/v1/platform/workspace/conversations/{conversation_id}` | Auth; Service resolves conversation and checks matter | Auth + Obj→M:R; owner-only for non-matter chat | OK via Service; return non-enumerating denial |
| POST | `/v1/platform/workspace/conversations/{conversation_id}/messages` | Auth; Service checks conversation/matter | Auth + Obj→M:W; validate author field server-side | PARTIAL — authorization exists; caller-controlled `author` must not impersonate system/assistant |
| POST | `/v1/platform/conversations` | Auth; Service checks optional matter | Auth + M:W when matter-bound | OK via Service |
| GET | `/v1/platform/conversations` | Auth; Service user-scopes list | Auth; user/tenant-owned only | OK via Service |
| GET | `/v1/platform/conversations/{conversation_id}` | Auth; Service resolves ownership/matter | Auth + Obj→M:R or conversation owner | OK via Service |
| POST | `/v1/platform/conversations/{conversation_id}/messages` | Auth; Service resolves ownership/matter | Auth + Obj→M:W; authorize every attachment Obj→M:R + RELEASED | PARTIAL — attachment authorization requires explicit proof |
| POST | `/v1/platform/conversations/{conversation_id}/messages/stream` | Auth at request; Service checks conversation | Same as send; generic stream errors, limits, cancellation/revocation policy | PARTIAL — emits internal `str(e)` and attachment/tool policy is incomplete |

## D. Matters, conflicts, and evidence (`/v1/platform`)

| Method | Route | Current control | Target policy | Status / action |
|---|---|---|---|---|
| POST | `/matters` | Auth; public-demo blocks non-synthetic; store creates in actor org | Auth + organization `matter:create` role; Demo | PARTIAL — no explicit role/capability beyond Auth |
| GET | `/matters` | Auth; store scopes by actor | Auth; only authorized matters | OK via Service |
| GET | `/matters/{matter_id}` | Auth; store calls deny-first matter access | Auth + M:R | OK via Service |
| POST | `/conflicts/check` | Auth; conflict service org-scoped; optional matter behavior not explicit at route | Auth + conflict-check capability; M:W when matter supplied | PARTIAL — enforce optional matter authorization explicitly |
| POST | `/matters/{matter_id}/documents/text` | Auth; evidence service requires M:W; Demo restrictions | Auth + M:W + Demo + quarantine policy | OK authorization; quarantine remains P0 |
| GET | `/matters/{matter_id}/documents` | Auth; evidence service checks matter access | Auth + M:R | OK via Service |
| POST | `/matters/{matter_id}/propositions` | Auth; evidence service requires M:W | Auth + M:W; referenced document/page Obj→same matter and RELEASED | PARTIAL — matter check exists; reference integrity authorization must be tested |

## E. Citations, knowledge, audit, and deadlines

| Method | Route | Current control | Target policy | Status / action |
|---|---|---|---|---|
| POST | `/v1/platform/citations/verify` | Auth; optional matter access helper defaults read | Auth + M:R if matter supplied; tenant-safe audit | OK |
| GET | `/v1/platform/knowledge/sources` | Auth | Auth; globally readable approved metadata | OK |
| GET | `/v1/platform/citations/audit` | Auth; optional M:R | Auth + M:R if matter supplied; organization scope if omitted | PARTIAL — empty matter must not expose global cross-tenant audit |
| GET | `/v1/platform/audit/verify` | Auth only; global chain verification | Auth + auditor/admin capability; tenant-safe summary or protected system operation | GAP |
| POST | `/v1/platform/deadlines/calculate` | Auth + explicit M:R | Auth + M:W (creates legal-work/audit artifact) and provisional state | PARTIAL — upgrade mutation requirement to M:W |
| POST | `/v1/deadlines/jr-clock` | Auth + explicit M:R | Auth + M:W and provisional state | PARTIAL — upgrade to M:W |
| POST | `/v1/deadlines/calculate` | Auth + explicit M:R | Auth + M:W and provisional state | PARTIAL — upgrade to M:W |
| GET | `/v1/knowledge/sources` | Auth | Auth; approved global metadata | OK |
| POST | `/v1/knowledge/citations/verify` | Auth; no matter parameter | Auth; global verification only, or add optional M:R and tenant audit | PARTIAL — duplicate path lacks matter-scoped provenance |

## F. Platform consent, export, and drafting routes

| Method | Route | Current control | Target policy | Status / action |
|---|---|---|---|---|
| POST | `/v1/platform/matters/{matter_id}/consents` | Auth; consent store requires M:W | Auth + M:W + consent-capture capability; actor attribution | OK baseline via Service |
| GET | `/v1/platform/matters/{matter_id}/consents` | Auth; store checks M:R | Auth + M:R | OK via Service |
| POST | `/v1/platform/consents/{consent_id}/withdraw` | Auth; store resolves consent and requires M:W | Auth + Obj→M:W; subject/authorized-operator policy | OK baseline via Service |
| GET | `/v1/platform/matters/{matter_id}/consents/evaluate-ai` | Auth only; store method called without user | Auth + M:R; processing purpose/model destination context | GAP — direct matter authorization missing |
| POST | `/v1/platform/matters/{matter_id}/exports/manifest` | Auth; service checks M:R; body contains approval booleans | Auth + M:W + export capability + State; approvals from persisted events, not request booleans | GAP — read-level and self-attested approval controls are insufficient |
| GET | `/v1/platform/matters/{matter_id}/exports/manifest` | Auth; service checks M:R | Auth + M:R | OK via Service |
| GET | `/v1/platform/matters/{matter_id}/drafts/form-66` | Auth; drafting service checks M:R | Auth + M:R; draft/non-court-ready state | OK baseline via Service |
| GET | `/v1/platform/matters/{matter_id}/drafts/form-67` | Auth; drafting service checks M:R | Auth + M:R; draft/non-court-ready state | OK baseline via Service |

## G. Duplicate HITL consent and exception routes (`backend/api/main.py`)

These routes use process-local HITL state and generally authenticate without matter authorization.

| Method | Route | Current control | Target policy | Status / action |
|---|---|---|---|---|
| POST | `/v1/matters/{matter_id}/consents` | Auth only | Auth + M:W + consent-capture capability | GAP |
| GET | `/v1/matters/{matter_id}/consents` | Auth only | Auth + M:R | GAP |
| POST | `/v1/consents/{consent_id}/withdraw` | Auth; global in-memory ID lookup | Auth + Obj→M:W + withdrawal policy | GAP |
| POST | `/v1/consents/evaluate-operation` | Auth; caller supplies matter | Auth + M:R; policy context bound to actor/org | GAP |
| POST | `/v1/matters/{matter_id}/exceptions` | Auth only | Auth + M:W | GAP |
| GET | `/v1/matters/{matter_id}/exceptions` | Auth only; filters global list by ID | Auth + M:R | GAP |
| POST | `/v1/exceptions/{exception_id}/resolve` | Auth; global ID lookup | Auth + Obj→M:W + reviewer capability + State | GAP |

**Required disposition:** consolidate duplicate consent paths behind the persisted platform service rather than maintaining competing authorization/state models.

## H. Production review and release routes (`backend/api/main.py`)

| Method | Route | Current control | Target policy | Status / action |
|---|---|---|---|---|
| POST | `/v1/matters/{matter_id}/productions/freeze` | Auth + Demo/text checks; no M check | Auth + M:W + export capability + State | GAP |
| POST | `/v1/productions/{production_id}/review` | Auth; global in-memory ID lookup | Auth + Obj→M:W + reviewer role + immutable snapshot + State | GAP |
| POST | `/v1/productions/{production_id}/approve` | Auth; global ID lookup; same-person override accepted | Auth + Obj→M:W + approver role + separation of duties + State | GAP |
| POST | `/v1/productions/{production_id}/release` | Auth + Demo; global ID lookup | Auth + Obj→M:W + release capability + all gates atomically satisfied | GAP |

## I. Post-resolution routes (`backend/api/main.py`)

| Method | Route | Current control | Target policy | Status / action |
|---|---|---|---|---|
| POST | `/v1/matters/{matter_id}/post-resolution/ingest` | Auth + Demo/text checks; no M check | Auth + M:W + post-resolution capability | GAP |
| GET | `/v1/matters/{matter_id}/post-resolution` | Auth only; process-global matter lookup | Auth + M:R | GAP |
| POST | `/v1/matters/{matter_id}/post-resolution/enforcement` | Auth only | Auth + M:W + enforcement-package capability + State | GAP |
| POST | `/v1/matters/{matter_id}/post-resolution/close` | Auth only | Auth + M:A or closure capability + State | GAP |

## J. Role and access-level target model

Current roles in SQL include `owner`, `admin`, `lawyer`, `paralegal`, `client`, `member`, and `readonly`; matter levels include `read`, `write`, `admin`, and deny state `ethical_wall`. The target must use capabilities rather than broad role checks alone.

| Capability | Default eligible roles | Matter level | Additional rule |
|---|---|---|---|
| `matter:create` | owner, admin, lawyer | organization | organization policy |
| `matter:read` | all assigned roles | read | ethical wall/revocation deny |
| `matter:write` | owner, admin, lawyer, paralegal, assigned member | write | client/readonly denied by default |
| `matter:admin` | owner, admin, responsible lawyer | admin | membership management audit |
| `consent:capture` | lawyer, authorized paralegal | write | subject/authentication evidence |
| `exception:resolve` | assigned human reviewer | write | cannot be automated actor |
| `production:review` | lawyer/authorized reviewer | write | snapshot-bound |
| `production:approve` | lawyer/authorized approver | write | distinct from reviewer unless audited emergency override |
| `production:release` | authorized lawyer/operator | write | all gates satisfied atomically |
| `matter:close` | owner/admin/responsible lawyer | admin | retention plan created |
| `audit:verify` | security auditor/admin | organization/system | tenant-safe scope |
| `conflict:check` | authorized intake/legal staff | organization or write | results restricted/audited |

Role-to-capability assignments must be configuration/policy data with tests; they must not be inferred only from route names.

## K. Required authorization test matrix

For every non-public route, parameterize these principals as applicable:

| Principal | Expected result |
|---|---|
| Missing/malformed/expired/revoked session | 401 |
| Active user in another organization | deny without object disclosure |
| Same organization, no membership | deny unless explicit owner/admin implicit-access policy and no denial |
| Explicit ethical wall | deny for every role including owner/admin |
| Revoked membership | deny |
| Read-only membership on GET | allow when no stricter capability/state rule |
| Read-only membership on mutation | deny |
| Writer on ordinary mutation | allow |
| Writer without special reviewer/approver capability | deny special transition |
| Authorized role with stale/invalid state | deny with safe conflict response |
| Authorized role and valid state | allow and audit |
| Cookie session without valid CSRF on mutation | 403 |

### Object-ID tests

For consent, exception, production, conversation, document/page, citation audit, export, attachment, and job IDs:

1. nonexistent ID and inaccessible existing ID follow the same disclosure policy;
2. object organization and matter are resolved inside the authorized transaction/RLS context;
3. child resources must belong to the supplied parent matter;
4. state checks occur after identity/object scope is established but before mutation;
5. authorization denial and successful material transitions are audited without sensitive payloads.

## L. Closure summary

| Classification | Count | Meaning |
|---|---:|---|
| Total declared application routes | 67 | Matches route inventory on baseline |
| Deliberately public | 18 | Static/health/design/public workspace/auth exchange/metadata, subject to hardening |
| Authenticated routes | 49 | Includes service-authorized and gap routes |
| Explicit/indirect baseline acceptable (`OK`) | 25 | Some still require non-auth P0 controls |
| Partial authorization/hardening | 20 | Control exists but target policy is incomplete |
| Direct authorization gaps | 22 | Must close before Gate 0 |

The status totals are route-review classifications, not a claim that `OK` routes are production-ready. Gate 0 requires automated evidence for all 67 routes and no unexplained `GAP` or `PARTIAL` authorization finding.
