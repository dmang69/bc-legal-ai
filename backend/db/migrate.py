"""Schema migrations for SQLite (always) and optional Postgres SQL files."""

from __future__ import annotations

from pathlib import Path

from backend.db.connection import get_connection, get_db_backend

_SQL_DIR = Path(__file__).resolve().parents[2] / "architecture" / "contracts" / "sql"

# SQLite-compatible core schema (subset of Postgres DDL)
SQLITE_SCHEMA = """
CREATE TABLE IF NOT EXISTS schema_migrations (
  id TEXT PRIMARY KEY,
  applied_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS organizations (
  org_id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'ACTIVE',
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS users (
  user_id TEXT PRIMARY KEY,
  org_id TEXT NOT NULL REFERENCES organizations(org_id),
  email TEXT NOT NULL UNIQUE,
  display_name TEXT NOT NULL DEFAULT '',
  password_hash TEXT NOT NULL,
  password_salt TEXT NOT NULL,
  role TEXT NOT NULL DEFAULT 'member',
  mfa_enabled INTEGER NOT NULL DEFAULT 0,
  status TEXT NOT NULL DEFAULT 'ACTIVE',
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  last_login_at TEXT
);

CREATE TABLE IF NOT EXISTS sessions (
  session_id TEXT PRIMARY KEY,
  user_id TEXT NOT NULL REFERENCES users(user_id),
  org_id TEXT NOT NULL REFERENCES organizations(org_id),
  token_hash TEXT NOT NULL UNIQUE,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  expires_at TEXT NOT NULL,
  revoked_at TEXT,
  user_agent TEXT NOT NULL DEFAULT '',
  ip_hint TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS matters (
  matter_id TEXT PRIMARY KEY,
  title TEXT NOT NULL DEFAULT '',
  org_id TEXT,
  status TEXT NOT NULL DEFAULT 'OPEN',
  client_label TEXT NOT NULL DEFAULT '',
  synthetic INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS matter_members (
  matter_id TEXT NOT NULL REFERENCES matters(matter_id) ON DELETE CASCADE,
  user_id TEXT NOT NULL REFERENCES users(user_id),
  access_level TEXT NOT NULL DEFAULT 'read',
  granted_at TEXT NOT NULL DEFAULT (datetime('now')),
  granted_by TEXT NOT NULL DEFAULT 'system',
  revoked_at TEXT,
  PRIMARY KEY (matter_id, user_id)
);

CREATE TABLE IF NOT EXISTS parties (
  party_id TEXT PRIMARY KEY,
  org_id TEXT NOT NULL REFERENCES organizations(org_id),
  display_name TEXT NOT NULL,
  name_normalized TEXT NOT NULL,
  party_type TEXT NOT NULL DEFAULT 'person',
  aliases TEXT NOT NULL DEFAULT '[]',
  addresses TEXT NOT NULL DEFAULT '[]',
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS matter_parties (
  matter_id TEXT NOT NULL REFERENCES matters(matter_id) ON DELETE CASCADE,
  party_id TEXT NOT NULL REFERENCES parties(party_id),
  role TEXT NOT NULL,
  PRIMARY KEY (matter_id, party_id, role)
);

CREATE TABLE IF NOT EXISTS conflict_checks (
  check_id TEXT PRIMARY KEY,
  org_id TEXT NOT NULL REFERENCES organizations(org_id),
  matter_id TEXT,
  query_name TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'PENDING_REVIEW',
  hits_json TEXT NOT NULL DEFAULT '[]',
  reviewer_id TEXT,
  waiver_notes TEXT NOT NULL DEFAULT '',
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  resolved_at TEXT
);

CREATE TABLE IF NOT EXISTS audit_ledger (
  seq INTEGER PRIMARY KEY AUTOINCREMENT,
  event_id TEXT NOT NULL UNIQUE,
  org_id TEXT NOT NULL DEFAULT '',
  matter_id TEXT NOT NULL DEFAULT '',
  actor_id TEXT NOT NULL,
  action TEXT NOT NULL,
  resource_type TEXT NOT NULL DEFAULT '',
  resource_id TEXT NOT NULL DEFAULT '',
  detail TEXT NOT NULL DEFAULT '{}',
  prev_hash TEXT NOT NULL,
  entry_hash TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS consents (
  consent_id TEXT PRIMARY KEY,
  matter_id TEXT NOT NULL REFERENCES matters(matter_id),
  subject_id TEXT NOT NULL,
  category TEXT NOT NULL,
  purpose TEXT NOT NULL,
  processing_scope TEXT NOT NULL DEFAULT '[]',
  model_scope TEXT NOT NULL DEFAULT 'PRIVATE_INFERENCE_ONLY',
  status TEXT NOT NULL,
  notice_version TEXT NOT NULL,
  granted_at TEXT,
  expires_at TEXT,
  withdrawn_at TEXT,
  captured_by TEXT NOT NULL DEFAULT 'system',
  authentication_event TEXT,
  signature_hash TEXT,
  plain_language TEXT NOT NULL DEFAULT '',
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS documents (
  document_id TEXT PRIMARY KEY,
  org_id TEXT NOT NULL,
  matter_id TEXT NOT NULL REFERENCES matters(matter_id),
  filename TEXT NOT NULL,
  content_type TEXT NOT NULL DEFAULT 'application/octet-stream',
  byte_size INTEGER NOT NULL DEFAULT 0,
  sha256 TEXT NOT NULL,
  storage_uri TEXT NOT NULL DEFAULT '',
  quarantine_status TEXT NOT NULL DEFAULT 'QUARANTINED',
  privilege_class TEXT NOT NULL DEFAULT 'UNKNOWN',
  synthetic INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  created_by TEXT NOT NULL DEFAULT 'system'
);

CREATE TABLE IF NOT EXISTS document_pages (
  page_id TEXT PRIMARY KEY,
  document_id TEXT NOT NULL REFERENCES documents(document_id) ON DELETE CASCADE,
  matter_id TEXT NOT NULL,
  page_number INTEGER NOT NULL,
  page_hash TEXT NOT NULL DEFAULT '',
  text_content TEXT NOT NULL DEFAULT '',
  ocr_confidence REAL,
  needs_review INTEGER NOT NULL DEFAULT 0,
  UNIQUE (document_id, page_number)
);

CREATE TABLE IF NOT EXISTS propositions (
  proposition_id TEXT PRIMARY KEY,
  matter_id TEXT NOT NULL REFERENCES matters(matter_id),
  document_id TEXT,
  page_id TEXT,
  span_start INTEGER,
  span_end INTEGER,
  text TEXT NOT NULL,
  classification TEXT NOT NULL DEFAULT 'UNCLASSIFIED',
  confidence REAL,
  human_confirmed INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS evidence_relationships (
  rel_id TEXT PRIMARY KEY,
  matter_id TEXT NOT NULL REFERENCES matters(matter_id),
  from_id TEXT NOT NULL,
  to_id TEXT NOT NULL,
  rel_type TEXT NOT NULL,
  detail TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS knowledge_sources (
  source_id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  authority_type TEXT NOT NULL,
  jurisdiction TEXT NOT NULL,
  permitted_content TEXT NOT NULL DEFAULT '[]',
  retrieval_method TEXT NOT NULL DEFAULT 'approved_connector',
  health_status TEXT NOT NULL DEFAULT 'UNKNOWN',
  terms_reviewed_at TEXT,
  last_successful_update TEXT
);

CREATE TABLE IF NOT EXISTS legal_test_registry (
  test_id TEXT PRIMARY KEY,
  title TEXT NOT NULL,
  jurisdiction TEXT NOT NULL DEFAULT 'BC',
  act_name TEXT NOT NULL DEFAULT '',
  section TEXT NOT NULL DEFAULT '',
  section_heading TEXT NOT NULL DEFAULT '',
  source_url TEXT NOT NULL DEFAULT '',
  source_hash TEXT NOT NULL DEFAULT '',
  expected_topic TEXT NOT NULL DEFAULT '',
  lifecycle_state TEXT NOT NULL DEFAULT 'DRAFT',
  human_verifier TEXT,
  version INTEGER NOT NULL DEFAULT 1,
  disabled INTEGER NOT NULL DEFAULT 0,
  body_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS citation_verifications (
  verification_id TEXT PRIMARY KEY,
  matter_id TEXT NOT NULL DEFAULT '',
  citation_text TEXT NOT NULL,
  status TEXT NOT NULL,
  source_id TEXT,
  source_url TEXT NOT NULL DEFAULT '',
  authority_type TEXT NOT NULL DEFAULT 'UNKNOWN',
  jurisdiction TEXT NOT NULL DEFAULT '',
  pinpoint TEXT NOT NULL DEFAULT '',
  expected_topic TEXT NOT NULL DEFAULT '',
  source_hash TEXT NOT NULL DEFAULT '',
  currency_date TEXT NOT NULL DEFAULT '',
  reasons TEXT NOT NULL DEFAULT '[]',
  verified_by TEXT NOT NULL DEFAULT 'system',
  court_ready INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS citation_audit_events (
  audit_id TEXT PRIMARY KEY,
  verification_id TEXT NOT NULL REFERENCES citation_verifications(verification_id),
  matter_id TEXT NOT NULL DEFAULT '',
  event_type TEXT NOT NULL,
  actor_id TEXT NOT NULL DEFAULT 'system',
  detail_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS export_manifests (
  manifest_id TEXT PRIMARY KEY,
  matter_id TEXT NOT NULL REFERENCES matters(matter_id),
  destination TEXT NOT NULL DEFAULT 'export',
  document_ids_json TEXT NOT NULL DEFAULT '[]',
  citation_ids_json TEXT NOT NULL DEFAULT '[]',
  status TEXT NOT NULL,
  court_ready INTEGER NOT NULL DEFAULT 0,
  privilege_decision_json TEXT NOT NULL DEFAULT '{}',
  blockers_json TEXT NOT NULL DEFAULT '[]',
  approvals_json TEXT NOT NULL DEFAULT '{}',
  created_by TEXT NOT NULL DEFAULT 'system',
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS workspace_conversations (
  conversation_id TEXT PRIMARY KEY,
  matter_id TEXT NOT NULL DEFAULT '',
  org_id TEXT NOT NULL DEFAULT '',
  title TEXT NOT NULL DEFAULT 'Workspace conversation',
  mode TEXT NOT NULL DEFAULT 'general',
  created_by TEXT NOT NULL DEFAULT 'system',
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS workspace_messages (
  message_id TEXT PRIMARY KEY,
  conversation_id TEXT NOT NULL REFERENCES workspace_conversations(conversation_id) ON DELETE CASCADE,
  matter_id TEXT NOT NULL DEFAULT '',
  author TEXT NOT NULL,
  body TEXT NOT NULL,
  metadata_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
"""


def _seed_sqlite(conn) -> None:
    conn.execute(
        """
        INSERT OR IGNORE INTO knowledge_sources
        (source_id, name, authority_type, jurisdiction, permitted_content, health_status)
        VALUES
        ('source_bc_laws', 'BC Laws', 'OFFICIAL_PRIMARY', 'BC',
         '["statutes","regulations","court_rules","point_in_time_versions"]', 'HEALTHY'),
        ('source_canlii', 'CanLII', 'SECONDARY', 'CA',
         '["cases","citation_relationships"]', 'MANUAL_REQUIRED')
        """
    )
    # Mark s.56 retaliation test disabled in registry
    conn.execute(
        """
        INSERT OR IGNORE INTO legal_test_registry
        (test_id, title, jurisdiction, act_name, section, section_heading,
         source_url, expected_topic, lifecycle_state, disabled, body_json)
        VALUES
        ('TEST-RETALIATORY-EVICTION-S56',
         'DISABLED: incorrect s.56 retaliation mapping',
         'BC',
         'Residential Tenancy Act',
         '56',
         'Application for order ending tenancy early (confirm on BC Laws)',
         'https://www.bclaws.gov.bc.ca/',
         'retaliatory_eviction',
         'DISABLED',
         1,
         '{"reason":"section-topic mismatch"}')
        """
    )


def apply_migrations() -> None:
    backend = get_db_backend()
    if backend == "sqlite":
        with get_connection() as conn:
            conn.executescript(SQLITE_SCHEMA)
            row = conn.execute(
                "SELECT 1 FROM schema_migrations WHERE id = ?", ("sqlite_m1_v1",)
            ).fetchone()
            if not row:
                _seed_sqlite(conn)
                conn.execute(
                    "INSERT INTO schema_migrations (id) VALUES (?)", ("sqlite_m1_v1",)
                )
        return

    # Postgres: run SQL files if present
    with get_connection() as conn:
        for name in ("phase3_core.sql", "m1_platform.sql"):
            path = _SQL_DIR / name
            if not path.is_file():
                continue
            sql = path.read_text(encoding="utf-8")
            # strip BEGIN/COMMIT for psycopg multi-statement
            conn.execute(sql)  # type: ignore[attr-defined]
