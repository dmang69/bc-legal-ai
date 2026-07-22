-- Phase 3 core tables — BC Legal AI Associate
-- Design locks: consent ≠ privilege; withdrawal ≠ hard delete; RTB archive partial.
-- Dev only until auth + RLS. Not legal advice.

BEGIN;

CREATE TABLE IF NOT EXISTS matters (
  matter_id       text PRIMARY KEY,
  title           text NOT NULL DEFAULT '',
  created_at      timestamptz NOT NULL DEFAULT now()
);

-- ---------------------------------------------------------------------------
-- Consent (processing only — no privilege columns)
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS consents (
  consent_id            text PRIMARY KEY,
  matter_id             text NOT NULL REFERENCES matters(matter_id),
  subject_id            text NOT NULL,
  category              text NOT NULL,
  purpose               text NOT NULL,
  processing_scope      jsonb NOT NULL DEFAULT '[]'::jsonb,
  model_scope           text NOT NULL DEFAULT 'PRIVATE_INFERENCE_ONLY',
  status                text NOT NULL,
  notice_version        text NOT NULL,
  granted_at            timestamptz,
  expires_at            timestamptz,
  withdrawn_at          timestamptz,
  captured_by           text NOT NULL DEFAULT 'system',
  authentication_event  text,
  signature_hash        text,
  plain_language        text NOT NULL DEFAULT '',
  created_at            timestamptz NOT NULL DEFAULT now(),
  updated_at            timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT consents_model_scope_chk CHECK (
    model_scope IN ('NONE', 'PRIVATE_INFERENCE_ONLY', 'EXTERNAL_MODEL')
  ),
  CONSTRAINT consents_no_blank_purpose CHECK (length(trim(purpose)) > 0)
);

CREATE INDEX IF NOT EXISTS consents_matter_idx ON consents(matter_id);
CREATE INDEX IF NOT EXISTS consents_subject_idx ON consents(subject_id);

CREATE TABLE IF NOT EXISTS consent_audit_events (
  entry_id     text PRIMARY KEY,
  ts           timestamptz NOT NULL DEFAULT now(),
  matter_id    text NOT NULL,
  subject_id   text NOT NULL,
  action       text NOT NULL,
  category     text NOT NULL DEFAULT '',
  consent_id   text,
  detail       text NOT NULL DEFAULT ''
  -- append-only: no UPDATE/DELETE grants in production role
);

CREATE TABLE IF NOT EXISTS consent_derived_artifacts (
  consent_id    text NOT NULL REFERENCES consents(consent_id),
  artifact_id   text NOT NULL,
  artifact_kind text NOT NULL,
  PRIMARY KEY (consent_id, artifact_id)
);

CREATE TABLE IF NOT EXISTS matter_processing_blocks (
  matter_id            text PRIMARY KEY REFERENCES matters(matter_id),
  optional_ai_blocked  boolean NOT NULL DEFAULT false,
  reason               text NOT NULL DEFAULT '',
  effective_at         timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS matter_legal_holds (
  matter_id    text PRIMARY KEY REFERENCES matters(matter_id),
  placed_at    timestamptz NOT NULL DEFAULT now(),
  placed_by    text NOT NULL,
  reason       text NOT NULL
);

-- ---------------------------------------------------------------------------
-- Exceptions
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS exceptions (
  exception_id                 text PRIMARY KEY,
  matter_id                    text NOT NULL REFERENCES matters(matter_id),
  task_id                      text,
  category                     text NOT NULL,
  severity                     text NOT NULL,
  summary                      text NOT NULL,
  affected_artifacts           jsonb NOT NULL DEFAULT '[]'::jsonb,
  raw_client_content_logged    boolean NOT NULL DEFAULT false,
  detected_by                  text NOT NULL DEFAULT 'system',
  model_id                     text,
  prompt_template_version      text,
  status                       text NOT NULL DEFAULT 'OPEN',
  assigned_reviewer            text,
  resolution                   text,
  resolution_by                text,
  freeze_export                boolean NOT NULL DEFAULT false,
  block_workflow               boolean NOT NULL DEFAULT false,
  proposed_content_quarantined boolean NOT NULL DEFAULT false,
  created_at                   timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT exceptions_no_raw_content CHECK (raw_client_content_logged = false),
  CONSTRAINT exceptions_severity_chk CHECK (
    severity IN ('INFO', 'NOTICE', 'WARNING', 'HIGH', 'CRITICAL')
  )
);

CREATE INDEX IF NOT EXISTS exceptions_matter_status_idx
  ON exceptions(matter_id, status);

-- ---------------------------------------------------------------------------
-- Approvals / productions
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS production_packages (
  production_id      text PRIMARY KEY,
  matter_id          text NOT NULL REFERENCES matters(matter_id),
  output_class       text NOT NULL,
  status             text NOT NULL,
  snapshot_hash      text NOT NULL,
  recipient          text NOT NULL DEFAULT '',
  reviewer_id        text,
  approver_id        text,
  same_person_override_reason text,
  manifest_json      jsonb,
  manifest_signature text,
  created_at         timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS approval_records (
  approval_id    text PRIMARY KEY,
  production_id  text NOT NULL REFERENCES production_packages(production_id),
  matter_id      text NOT NULL,
  stage          text NOT NULL,
  actor_id       text NOT NULL,
  decision       text NOT NULL,
  snapshot_hash  text NOT NULL,
  notes          text NOT NULL DEFAULT '',
  ts             timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT approval_stage_chk CHECK (stage IN ('REVIEW', 'APPROVE'))
);

-- ---------------------------------------------------------------------------
-- Knowledge sources
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS knowledge_sources (
  source_id               text PRIMARY KEY,
  name                    text NOT NULL,
  authority_type          text NOT NULL,
  jurisdiction            text NOT NULL,
  permitted_content       jsonb NOT NULL DEFAULT '[]'::jsonb,
  retrieval_method        text NOT NULL DEFAULT 'approved_connector',
  health_status           text NOT NULL DEFAULT 'UNKNOWN',
  terms_reviewed_at       timestamptz,
  last_successful_update  timestamptz,
  CONSTRAINT knowledge_authority_chk CHECK (
    authority_type IN ('OFFICIAL_PRIMARY', 'SECONDARY')
  )
);

CREATE TABLE IF NOT EXISTS statutory_provisions (
  provision_id     text PRIMARY KEY,
  source_id        text NOT NULL REFERENCES knowledge_sources(source_id),
  act              text NOT NULL,
  section          text NOT NULL,
  text             text NOT NULL,
  effective_from   date,
  effective_to     date,
  source_version   text NOT NULL DEFAULT '',
  source_hash      text NOT NULL DEFAULT '',
  retrieval_date   date
);

CREATE TABLE IF NOT EXISTS rtb_decisions (
  decision_id             text PRIMARY KEY,
  citation_or_file        text NOT NULL DEFAULT '',
  publication_source      text NOT NULL DEFAULT 'BC_RTB_ARCHIVE',
  publication_category    text NOT NULL DEFAULT '',
  archive_coverage        text NOT NULL DEFAULT 'PARTIAL',
  anonymization_status    text NOT NULL DEFAULT 'UNKNOWN',
  precedential_weight     text NOT NULL DEFAULT 'NON_BINDING_TRIBUNAL',
  completeness_warning    text NOT NULL DEFAULT
    'RTB decision archive coverage is partial by historical publication ranges and categories. Absence from the archive is not proof that no decision exists.',
  official_url            text,
  CONSTRAINT rtb_archive_partial_chk CHECK (archive_coverage = 'PARTIAL')
);

CREATE TABLE IF NOT EXISTS analysis_snapshots (
  knowledge_snapshot_id         text PRIMARY KEY,
  matter_id                     text NOT NULL REFERENCES matters(matter_id),
  statutory_version_ids         jsonb NOT NULL DEFAULT '[]'::jsonb,
  rules_version_ids             jsonb NOT NULL DEFAULT '[]'::jsonb,
  template_version_ids          jsonb NOT NULL DEFAULT '[]'::jsonb,
  authority_verification_time   timestamptz NOT NULL DEFAULT now(),
  analysis_ref                  text NOT NULL,
  change_notices                jsonb NOT NULL DEFAULT '[]'::jsonb,
  created_at                    timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS templates (
  template_id      text PRIMARY KEY,
  form_number      text NOT NULL DEFAULT '',
  document_type    text NOT NULL,
  forum            text NOT NULL DEFAULT '',
  source_rule      text NOT NULL DEFAULT '',
  status           text NOT NULL DEFAULT 'CURRENT',
  title            text NOT NULL,
  CONSTRAINT form_66_is_petition CHECK (
    form_number <> '66' OR document_type = 'PETITION'
  ),
  CONSTRAINT form_67_is_response CHECK (
    form_number <> '67' OR document_type = 'RESPONSE_TO_PETITION'
  )
);

-- Seed critical form rows
INSERT INTO templates (template_id, form_number, document_type, forum, source_rule, title)
VALUES
  ('bcsc_form_66_jr', '66', 'PETITION', 'BC_SUPREME_COURT', 'Rule 16-1', 'Petition (Form 66)'),
  ('bcsc_form_67_response', '67', 'RESPONSE_TO_PETITION', 'BC_SUPREME_COURT', 'Rule 16-1', 'Response to Petition (Form 67)'),
  ('bcsc_form_32', '32', 'NOTICE_OF_APPLICATION', 'BC_SUPREME_COURT', 'SCR', 'Notice of Application (Form 32)'),
  ('bcsc_form_33', '33', 'APPLICATION_RESPONSE', 'BC_SUPREME_COURT', 'SCR', 'Application Response (Form 33)'),
  ('bcsc_form_109', '109', 'AFFIDAVIT', 'BC_SUPREME_COURT', 'SCR', 'Affidavit (Form 109)')
ON CONFLICT (template_id) DO NOTHING;

INSERT INTO knowledge_sources (source_id, name, authority_type, jurisdiction, permitted_content, health_status)
VALUES
  ('source_bc_laws', 'BC Laws', 'OFFICIAL_PRIMARY', 'BC',
   '["statutes","regulations","court_rules","point_in_time_versions"]'::jsonb, 'HEALTHY'),
  ('source_canlii', 'CanLII', 'SECONDARY', 'CA',
   '["cases","citation_relationships"]'::jsonb, 'MANUAL_REQUIRED')
ON CONFLICT (source_id) DO NOTHING;

-- Messaging honesty constraint helper table
CREATE TABLE IF NOT EXISTS messaging_settings (
  matter_id                text PRIMARY KEY REFERENCES matters(matter_id),
  encryption_model         text NOT NULL,
  e2e_claimed              boolean NOT NULL DEFAULT false,
  server_side_ai_enabled   boolean NOT NULL DEFAULT false,
  CONSTRAINT messaging_honesty_chk CHECK (
    NOT (e2e_claimed = true AND server_side_ai_enabled = true)
  ),
  CONSTRAINT messaging_model_chk CHECK (
    encryption_model IN ('MODEL_A_E2EE', 'MODEL_B_WORKSPACE')
  )
);

COMMIT;
