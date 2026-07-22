-- M1 Secure Platform Foundation
-- Modular monolith tables: identity, isolation, conflicts, consent, audit, evidence.
-- Append-only audit_ledger: application never UPDATE/DELETE rows.
-- Not legal advice.

BEGIN;

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ---------------------------------------------------------------------------
-- Organizations & users
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS organizations (
  org_id          text PRIMARY KEY,
  name            text NOT NULL,
  status          text NOT NULL DEFAULT 'ACTIVE',
  created_at      timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS users (
  user_id         text PRIMARY KEY,
  org_id          text NOT NULL REFERENCES organizations(org_id),
  email           text NOT NULL UNIQUE,
  display_name    text NOT NULL DEFAULT '',
  password_hash   text NOT NULL,
  password_salt   text NOT NULL,
  role            text NOT NULL DEFAULT 'member',
  mfa_enabled     boolean NOT NULL DEFAULT false,
  status          text NOT NULL DEFAULT 'ACTIVE',
  created_at      timestamptz NOT NULL DEFAULT now(),
  last_login_at   timestamptz,
  CONSTRAINT users_role_chk CHECK (
    role IN ('owner', 'admin', 'lawyer', 'paralegal', 'client', 'member', 'readonly')
  ),
  CONSTRAINT users_status_chk CHECK (
    status IN ('ACTIVE', 'SUSPENDED', 'DELETED')
  )
);

CREATE INDEX IF NOT EXISTS users_org_idx ON users(org_id);

CREATE TABLE IF NOT EXISTS sessions (
  session_id      text PRIMARY KEY,
  user_id         text NOT NULL REFERENCES users(user_id),
  org_id          text NOT NULL REFERENCES organizations(org_id),
  token_hash      text NOT NULL UNIQUE,
  created_at      timestamptz NOT NULL DEFAULT now(),
  expires_at      timestamptz NOT NULL,
  revoked_at      timestamptz,
  user_agent      text NOT NULL DEFAULT '',
  ip_hint         text NOT NULL DEFAULT ''
);

CREATE INDEX IF NOT EXISTS sessions_user_idx ON sessions(user_id);

-- Extend matters for multi-tenant isolation
ALTER TABLE matters ADD COLUMN IF NOT EXISTS org_id text;
ALTER TABLE matters ADD COLUMN IF NOT EXISTS status text NOT NULL DEFAULT 'OPEN';
ALTER TABLE matters ADD COLUMN IF NOT EXISTS client_label text NOT NULL DEFAULT '';
ALTER TABLE matters ADD COLUMN IF NOT EXISTS synthetic boolean NOT NULL DEFAULT false;
ALTER TABLE matters ADD COLUMN IF NOT EXISTS updated_at timestamptz NOT NULL DEFAULT now();

CREATE INDEX IF NOT EXISTS matters_org_idx ON matters(org_id);

CREATE TABLE IF NOT EXISTS matter_members (
  matter_id       text NOT NULL REFERENCES matters(matter_id) ON DELETE CASCADE,
  user_id         text NOT NULL REFERENCES users(user_id),
  access_level    text NOT NULL DEFAULT 'read',
  granted_at      timestamptz NOT NULL DEFAULT now(),
  granted_by      text NOT NULL DEFAULT 'system',
  revoked_at      timestamptz,
  PRIMARY KEY (matter_id, user_id),
  CONSTRAINT matter_access_chk CHECK (
    access_level IN ('read', 'write', 'admin', 'ethical_wall')
  )
);

-- ---------------------------------------------------------------------------
-- Conflict parties
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS parties (
  party_id        text PRIMARY KEY,
  org_id          text NOT NULL REFERENCES organizations(org_id),
  display_name    text NOT NULL,
  name_normalized text NOT NULL,
  party_type      text NOT NULL DEFAULT 'person',
  aliases         jsonb NOT NULL DEFAULT '[]'::jsonb,
  addresses       jsonb NOT NULL DEFAULT '[]'::jsonb,
  created_at      timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS parties_org_name_idx ON parties(org_id, name_normalized);

CREATE TABLE IF NOT EXISTS matter_parties (
  matter_id       text NOT NULL REFERENCES matters(matter_id) ON DELETE CASCADE,
  party_id        text NOT NULL REFERENCES parties(party_id),
  role            text NOT NULL,
  PRIMARY KEY (matter_id, party_id, role),
  CONSTRAINT party_role_chk CHECK (
    role IN ('client', 'former_client', 'opposing', 'witness', 'counsel', 'other')
  )
);

CREATE TABLE IF NOT EXISTS conflict_checks (
  check_id        text PRIMARY KEY,
  org_id          text NOT NULL REFERENCES organizations(org_id),
  matter_id       text REFERENCES matters(matter_id),
  query_name      text NOT NULL,
  status          text NOT NULL DEFAULT 'PENDING_REVIEW',
  hits_json       jsonb NOT NULL DEFAULT '[]'::jsonb,
  reviewer_id     text,
  waiver_notes    text NOT NULL DEFAULT '',
  created_at      timestamptz NOT NULL DEFAULT now(),
  resolved_at     timestamptz
);

-- ---------------------------------------------------------------------------
-- Hash-chained append-only audit ledger
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS audit_ledger (
  seq             bigserial PRIMARY KEY,
  event_id        text NOT NULL UNIQUE,
  org_id          text NOT NULL DEFAULT '',
  matter_id       text NOT NULL DEFAULT '',
  actor_id        text NOT NULL,
  action          text NOT NULL,
  resource_type   text NOT NULL DEFAULT '',
  resource_id     text NOT NULL DEFAULT '',
  detail          jsonb NOT NULL DEFAULT '{}'::jsonb,
  prev_hash       text NOT NULL,
  entry_hash      text NOT NULL,
  created_at      timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS audit_ledger_matter_idx ON audit_ledger(matter_id, seq);
CREATE INDEX IF NOT EXISTS audit_ledger_org_idx ON audit_ledger(org_id, seq);

-- ---------------------------------------------------------------------------
-- Evidence Matrix (M2 foundation)
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS documents (
  document_id     text PRIMARY KEY,
  org_id          text NOT NULL,
  matter_id       text NOT NULL REFERENCES matters(matter_id),
  filename        text NOT NULL,
  content_type    text NOT NULL DEFAULT 'application/octet-stream',
  byte_size       bigint NOT NULL DEFAULT 0,
  sha256          text NOT NULL,
  storage_uri     text NOT NULL DEFAULT '',
  quarantine_status text NOT NULL DEFAULT 'QUARANTINED',
  privilege_class text NOT NULL DEFAULT 'UNKNOWN',
  synthetic       boolean NOT NULL DEFAULT false,
  created_at      timestamptz NOT NULL DEFAULT now(),
  created_by      text NOT NULL DEFAULT 'system',
  CONSTRAINT doc_quarantine_chk CHECK (
    quarantine_status IN ('QUARANTINED', 'SCANNING', 'CLEAN', 'BLOCKED', 'RELEASED')
  )
);

CREATE INDEX IF NOT EXISTS documents_matter_idx ON documents(matter_id);

CREATE TABLE IF NOT EXISTS document_pages (
  page_id         text PRIMARY KEY,
  document_id     text NOT NULL REFERENCES documents(document_id) ON DELETE CASCADE,
  matter_id       text NOT NULL,
  page_number     int NOT NULL,
  page_hash       text NOT NULL DEFAULT '',
  text_content    text NOT NULL DEFAULT '',
  ocr_confidence  real,
  needs_review    boolean NOT NULL DEFAULT false,
  UNIQUE (document_id, page_number)
);

CREATE TABLE IF NOT EXISTS propositions (
  proposition_id  text PRIMARY KEY,
  matter_id       text NOT NULL REFERENCES matters(matter_id),
  document_id     text REFERENCES documents(document_id),
  page_id         text REFERENCES document_pages(page_id),
  span_start      int,
  span_end        int,
  text            text NOT NULL,
  classification  text NOT NULL DEFAULT 'UNCLASSIFIED',
  confidence      real,
  human_confirmed boolean NOT NULL DEFAULT false,
  created_at      timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT prop_class_chk CHECK (
    classification IN (
      'UNCLASSIFIED', 'FACT', 'ALLEGATION', 'LEGAL_ARGUMENT',
      'INFERENCE', 'ASSUMPTION', 'RECOMMENDATION'
    )
  )
);

CREATE INDEX IF NOT EXISTS propositions_matter_idx ON propositions(matter_id);

CREATE TABLE IF NOT EXISTS evidence_relationships (
  rel_id          text PRIMARY KEY,
  matter_id       text NOT NULL REFERENCES matters(matter_id),
  from_id         text NOT NULL,
  to_id           text NOT NULL,
  rel_type        text NOT NULL,
  detail          jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at      timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS evidence_rel_matter_idx ON evidence_relationships(matter_id);

-- ---------------------------------------------------------------------------
-- Legal test registry lifecycle
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS legal_test_registry (
  test_id         text PRIMARY KEY,
  title           text NOT NULL,
  jurisdiction    text NOT NULL DEFAULT 'BC',
  act_name        text NOT NULL DEFAULT '',
  section         text NOT NULL DEFAULT '',
  section_heading text NOT NULL DEFAULT '',
  source_url      text NOT NULL DEFAULT '',
  source_hash     text NOT NULL DEFAULT '',
  expected_topic  text NOT NULL DEFAULT '',
  lifecycle_state text NOT NULL DEFAULT 'DRAFT',
  human_verifier  text,
  version         int NOT NULL DEFAULT 1,
  disabled        boolean NOT NULL DEFAULT false,
  body_json       jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at      timestamptz NOT NULL DEFAULT now(),
  updated_at      timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT legal_test_lifecycle_chk CHECK (
    lifecycle_state IN (
      'DRAFT', 'SOURCE_VERIFIED', 'LEGAL_REVIEW', 'APPROVED',
      'ACTIVE', 'SUPERSEDED', 'DISABLED'
    )
  )
);

COMMIT;
