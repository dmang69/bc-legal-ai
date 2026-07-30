# Structured feature options

Canonical catalog of BC Legal AI Platform capabilities.

| | |
|--|--|
| **API** | `GET /v1/platform/features` |
| **Code** | `backend/platform/feature_options.py` |
| **UI** | Work panel → **Features** |
| **Also embedded in** | `GET /v1/platform/ai/suite` → `feature_options` |

## Categories

| ID | Label |
|----|--------|
| `install` | Install & clients (Windows, macOS, Linux, Android, iOS, Chrome PWA) |
| `ai` | AI suite (Puter, Kimi, OpenClaw, Arena, Ollama, cloud LLMs) |
| `legal` | Legal tooling (JR clock, citations, Form 66, skills, ACL) |
| `productivity` | Summarize, email, research, code, web research |
| `governance` | Auth, audit, quotas, court_ready fail-closed |

## Option shape

```json
{
  "id": "ai.openclaw",
  "name": "OpenClaw agent harness",
  "category": "ai",
  "description": "...",
  "status": "live",
  "default_enabled": true,
  "org_toggleable": true,
  "enabled": true,
  "env_gate": "",
  "endpoints": ["/v1/platform/ai/openclaw/run"],
  "providers": [],
  "platforms": ["api", "chrome", "windows"],
  "safety_locks": ["no_autonomous_file_serve_settle"],
  "docs": "..."
}
```

## Selection guides (API `selection_guide`)

| Bundle | Intent |
|--------|--------|
| `pilot_synthetic` | Puter + OpenClaw + Arena + legal gates (no external cloud LLM) |
| `private_sensitive` | Ollama + safe_local + ACL + audit |
| `full_desktop` | Windows/macOS/PWA install surfaces + desktop autoupdate |

## Locks (always)

- Not legal advice  
- `court_ready` false by default  
- No autonomous filing / service / settlement / privilege waiver  
- External server LLMs fail-closed until env + org enable  

## Filter by category

```http
GET /v1/platform/features?category=ai
```
