# Architecture Overview

## System Architecture

BC Legal AI Associate is a **modular monolith** designed for supervised legal research, evidence management, and drafting support.

```
┌─────────────────────────────────────────────────────┐
│                   Client Layer                        │
│  ┌──────────┐  ┌──────────┐  ┌──────┐  ┌────────┐   │
│  │  Web PWA │  │  Tauri   │  │ API  │  │Mobile  │   │
│  │ (React)  │  │ Desktop  │  │ Docs │  │  App   │   │
│  └────┬─────┘  └────┬─────┘  └──┬───┘  └────┬───┘   │
└───────┼──────────────┼──────────┼─────────────┼───────┘
        │              │          │             │
┌───────┼──────────────┼──────────┼─────────────┼───────┐
│       ▼              ▼          ▼             ▼       │
│              FastAPI Gateway (backend/api/)           │
│  ┌──────────────────────────────────────────────────┐ │
│  │                Platform Routes                     │ │
│  │  /v1/platform/*  |  /v1/*  |  /health/*          │ │
│  └──────────────────────┬───────────────────────────┘ │
│                         │                              │
│  ┌──────────────────────▼───────────────────────────┐ │
│  │              Service Layer                         │ │
│  │  ┌────────┐ ┌──────┐ ┌────────┐ ┌───────────┐    │ │
│  │  │Identity│ │Matter│ │Evidence│ │Citation   │    │ │
│  │  │Service │ │Store │ │Service │ │Verifier   │    │ │
│  │  └────────┘ └──────┘ └────────┘ └───────────┘    │ │
│  │  ┌────────┐ ┌──────┐ ┌────────┐ ┌───────────┐    │ │
│  │  │Audit   │ │HITL  │ │Post-   │ │Deadline   │    │ │
│  │  │Ledger  │ │Ctrl  │ │Resol'n │ │Engine     │    │ │
│  │  └────────┘ └──────┘ └────────┘ └───────────┘    │ │
│  └──────────────────────┬───────────────────────────┘ │
│                         │                              │
│  ┌──────────────────────▼───────────────────────────┐ │
│  │              Data Layer                            │ │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐        │ │
│  │  │PostgreSQL│  │  Redis   │  │  MinIO   │        │ │
│  │  │ (Primary)│  │ (Queue)  │  │ (Blob)   │        │ │
│  │  └──────────┘  └──────────┘  └──────────┘        │ │
│  └──────────────────────────────────────────────────┘ │
└───────────────────────────────────────────────────────┘
```

## Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| **Modular Monolith** | Simpler than microservices for a legal pilot; deploy as one container, scale horizontally |
| **PostgreSQL First** | Row-level security (RLS), advisory locks, JSONB, pgvector, ACID compliance |
| **Fail-Closed** | All citation verification defaults `court_ready=false`; ethical walls cannot be bypassed by role |
| **Append-Only Audit** | Hash-chained ledger with cryptographic verification of chain integrity |
| **RAG-First AI** | Retrieval-Augmented Generation over verified sources; no autonomous model inference on client data |

## Data Flow

```
Client → API Gateway → Auth → Matter AuthZ → Service → Audit → DB
                         ↓                        ↓
                   Ethical Wall Check        Hash Chain Append
