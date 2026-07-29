# Conversational AI Legal Workspace Specification

**Status:** Controlling product/interface definition (2026-07-22)  
**Parent product:** [`PRODUCT_DESCRIPTION.md`](PRODUCT_DESCRIPTION.md)  
**Delivery shells:** Section G / Tauri / PWA — the **container only**

## 1. Product definition

BC Legal AI Associate is **not** merely a DMS, forms app, client portal, prompt pack, or case dashboard.

It is a **conversational AI legal operating environment**.

Primary interaction is natural conversation (text, voice, files, tools, agents). Responses include conversational answers, cited research, evidence links, structured analysis, timelines, warnings, forms, documents, tasks, agent activity, and downloadable work products.

**Inspirations (not copies):** Claude projects, Monica multi-tool assistants, Grok research+files, Copilot agents, Kimi document/agent workflows, Poe multi-bot selection, Ollama private local models — plus **BC-specific** isolation, privilege, citation, and court controls.

## 2. Core interface — three panels

```text
LEFT SIDEBAR          MAIN CONVERSATION           WORK PANEL
New Chat              Messages + tools            Sources / Evidence /
Matters               Citations + approvals       Draft / Timeline /
Projects              Composer                    Agent / Audit
Agents
Documents …
```

## 3. Conversation types

| Type | Access |
|------|--------|
| General Chat | No automatic confidential matter access |
| Matter Chat | Locked to one matter ACL |
| Document Chat | Selected documents; page/timestamp cites |
| Research Chat | Official sources + verification |
| Drafting Chat | Live document beside chat |
| Agent Task Chat | Multi-step plan with Approve/Edit/Cancel |

## 4. Hard controls (never optional)

- Matter isolation and ethical walls  
- Consent and privilege gates  
- Citation verification before court-ready  
- Human confirmation for definitive deadlines  
- Agents cannot file, settle, waive privilege, send significant mail alone  
- No silent conversion of allegation → confirmed fact  

## 5. Interface build phases

| Phase | Build |
|-------|--------|
| **IF-1** (this scaffold) | Chat UI, history, matter selector, attachments meta, streaming, sources panel, mode selector, document preview cards, auth |
| **IF-2** | Projects, matter memory, artifact editor, agent plans, research mode, voice, Evidence Matrix, approvals |
| **IF-3** | Ollama, browser extension, email/calendar, automations, custom assistants, camera, offline |
| **IF-4** | Multi-agent teams, model comparison, plugins, desktop actions, org admin, cost dashboards |

## 6. Completion standard

See §28 of full program notes: persistent chats, matter-restricted chats, page-level citations, official law search, voice, models, agents, side-by-side drafts, evidence/chronology, Ollama, approvals, DOCX/PDF, same UX on web/desktop/mobile.

## 7. Implementation map (repo)

| Path | Role |
|------|------|
| `apps/platform-ui/` | Conversational workspace UI |
| `backend/platform/conversation.py` | Chat persistence + assistant orchestrator (scaffold) |
| `/v1/platform/conversations/*` | API |
| `packages/*` | Future extracted UI packages |
