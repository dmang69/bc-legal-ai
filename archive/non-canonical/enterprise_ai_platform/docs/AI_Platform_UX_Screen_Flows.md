# AI Platform UX + Screen Flows

## Primary UX Goal
Provide a familiar AI workspace with the speed of ChatGPT, the document depth of Claude, the multi-tool flexibility of Monica, the coding assist feel of Copilot, and the research discipline of Kimi.

## Main Navigation
- New Chat
- Workspaces
- Matters / Projects
- Knowledge
- Prompts
- Templates
- Compare
- Artifacts
- Admin
- Settings

## Main Layout
### Left Sidebar
- organization switcher
- workspace list
- recent chats
- pinned chats
- saved prompts
- create buttons

### Center Panel
- active chat thread
- message composer
- upload tray
- mode chips: General / Legal / Research / Code
- model selector
- follow-up suggestions

### Right Panel
- citations
- files in current workspace
- artifact preview
- extracted notes
- task checklist
- matter metadata

## Key Flows
### 1. New Chat
1. Click **New Chat**
2. Select workspace or create one
3. Choose mode
4. Choose model
5. Ask question
6. Attach files optionally
7. Save/export/pin/share result

### 2. Create Matter Workspace
1. Click **Workspaces**
2. New workspace
3. Name matter/project
4. Set type: General, Legal, Developer, Research
5. Add tags, team members, confidentiality level
6. Upload initial documents

### 3. Legal Drafting Flow
1. Open matter
2. Switch to **Legal** mode
3. Upload pleadings, notices, evidence, decisions
4. Ask for issue matrix / chronology / draft
5. Review structured output:
   - Facts
   - Assumptions
   - Issues
   - Authorities to verify
   - Draft argument
   - Remedy requested
6. Save as artifact
7. Route for human review

### 4. Research Flow
1. Switch to **Research** mode
2. Ask a broad question
3. Platform decomposes question into sub-issues
4. Returns research memo with open questions
5. User saves notes into workspace knowledge

### 5. Code Copilot Flow
1. Switch to **Code** mode
2. Paste code or upload repo summary
3. Ask for architecture, fixes, refactors, tests
4. Export structured diff or markdown plan

### 6. Prompt Library Flow
1. Open **Prompts**
2. Create reusable prompt template
3. Mark scope: personal, team, org
4. Attach default mode/model/settings
5. Reuse inside chat with one click

### 7. Compare Models Flow
1. Open **Compare**
2. Choose two models
3. Ask one prompt
4. Side-by-side outputs render
5. User picks best result and saves it

## Admin Console
### Tabs
- users
- roles
- workspaces
- providers
- usage
- audits
- policies

### Admin Actions
- invite member
- assign role
- disable provider
- set org prompt policies
- view audit events
- manage retention

## Design Guidelines
- fast keyboard-first workflow
- few clicks to first answer
- keep advanced settings visible but not noisy
- structured outputs in legal mode
- explain uncertainty, citations, and missing evidence clearly
- separate answer content from source/provenance panel

## MVP UX Priorities
- smooth chat
- workspace creation
- file upload
- model switcher
- mode switcher
- prompt library
- admin basics
- artifact save/export

## Later UX Additions
- browser extension
- voice input/output
- command palette
- multi-agent view
- live collaboration
- timeline and evidence board
- filing package builder