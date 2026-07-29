-- =============================================================================
-- BC Legal AI Associate — Data Model & Evidence Schema v1.0
-- PostgreSQL 16+ · pgvector · controlling production schema (2026-07-22)
-- Encryption: AES-256-GCM at rest (infra); TLS 1.3 in transit
-- =============================================================================
-- Design principles:
--   Matter isolation (RLS) · Evidence provenance · Privilege-aware
--   Audit-first · Temporal accuracy · Consent-bound
-- =============================================================================

BEGIN;

CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "citext";
CREATE EXTENSION IF NOT EXISTS "vector";

-- ---------------------------------------------------------------------------
-- 3.1 Users & authentication
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS users (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email           CITEXT NOT NULL UNIQUE,
    display_name    TEXT NOT NULL,
    password_hash   TEXT,
    password_salt   TEXT,
    mfa_secret      TEXT,
    mfa_enabled     BOOLEAN NOT NULL DEFAULT false,
    status          TEXT NOT NULL DEFAULT 'pending'
                    CHECK (status IN ('pending', 'active', 'suspended', 'deactivated')),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_login_at   TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS roles (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name            TEXT NOT NULL UNIQUE
                    CHECK (name IN (
                        'system_admin', 'lawyer', 'articled_student', 'paralegal',
                        'client', 'self_represented', 'expert', 'witness', 'auditor'
                    )),
    description     TEXT
);

CREATE TABLE IF NOT EXISTS user_roles (
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role_id         UUID NOT NULL REFERENCES roles(id),
    granted_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    granted_by      UUID REFERENCES users(id),
    PRIMARY KEY (user_id, role_id)
);

CREATE TABLE IF NOT EXISTS devices (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    device_name     TEXT NOT NULL,
    platform        TEXT NOT NULL
                    CHECK (platform IN ('windows', 'macos', 'android', 'ios', 'web_pwa')),
    os_version      TEXT,
    app_version     TEXT,
    fingerprint     TEXT NOT NULL UNIQUE,
    last_seen_at    TIMESTAMPTZ,
    is_trusted      BOOLEAN NOT NULL DEFAULT false,
    revoked_at      TIMESTAMPTZ,
    revoked_by      UUID REFERENCES users(id),
    revoked_reason  TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_devices_user ON devices(user_id);
CREATE INDEX IF NOT EXISTS idx_devices_fingerprint ON devices(fingerprint);

CREATE TABLE IF NOT EXISTS sessions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    device_id       UUID REFERENCES devices(id) ON DELETE SET NULL,
    token_hash      TEXT NOT NULL,
    ip_address      INET,
    user_agent      TEXT,
    expires_at      TIMESTAMPTZ NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    terminated_at   TIMESTAMPTZ,
    terminated_by   UUID REFERENCES users(id),
    terminate_reason TEXT
);

CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_expires ON sessions(expires_at);
CREATE INDEX IF NOT EXISTS idx_sessions_token ON sessions(token_hash);

-- ---------------------------------------------------------------------------
-- 3.2 Matters (create before evidence; timeline after evidence_documents)
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS matters (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title           TEXT NOT NULL,
    matter_number   TEXT NOT NULL UNIQUE,
    description     TEXT,
    forum           TEXT NOT NULL
                    CHECK (forum IN (
                        'residential_tenancy_branch', 'bc_supreme_court',
                        'bc_provincial_court', 'bc_court_of_appeal',
                        'supreme_court_of_canada', 'bc_human_rights_tribunal',
                        'administrative_tribunal_other', 'personal_organization'
                    )),
    matter_type     TEXT NOT NULL
                    CHECK (matter_type IN (
                        'tenancy_dispute', 'judicial_review', 'civil_litigation',
                        'administrative_hearing', 'personal_records', 'other'
                    )),
    notice_type     TEXT,
    status          TEXT NOT NULL DEFAULT 'intake'
                    CHECK (status IN (
                        'intake', 'active', 'pending_client', 'pending_court',
                        'in_drafting', 'under_review', 'filed', 'resolved',
                        'enforcement', 'archived', 'closed'
                    )),
    limitation_date DATE,
    next_hearing_date DATE,
    filed_date      DATE,
    resolved_date   DATE,
    is_demo         BOOLEAN NOT NULL DEFAULT false,
    is_archived     BOOLEAN NOT NULL DEFAULT false,
    created_by      UUID NOT NULL REFERENCES users(id),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_matters_status ON matters(status);
CREATE INDEX IF NOT EXISTS idx_matters_forum ON matters(forum);
CREATE INDEX IF NOT EXISTS idx_matters_created_by ON matters(created_by);

CREATE TABLE IF NOT EXISTS matter_participants (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    matter_id       UUID NOT NULL REFERENCES matters(id) ON DELETE CASCADE,
    user_id         UUID REFERENCES users(id) ON DELETE SET NULL,
    external_name   TEXT,
    external_email  TEXT,
    role            TEXT NOT NULL
                    CHECK (role IN (
                        'lead_lawyer', 'associate', 'articled_student', 'paralegal',
                        'client', 'opposing_party', 'opposing_counsel',
                        'expert_witness', 'factual_witness', 'adjudicator',
                        'registrar', 'other'
                    )),
    access_level    TEXT NOT NULL DEFAULT 'standard'
                    CHECK (access_level IN (
                        'full', 'standard', 'client_view', 'limited', 'no_access'
                    )),
    privilege_access BOOLEAN NOT NULL DEFAULT false,
    active          BOOLEAN NOT NULL DEFAULT true,
    joined_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    left_at         TIMESTAMPTZ
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_matter_participants_unique_user
    ON matter_participants(matter_id, user_id, role)
    WHERE user_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_matter_participants_matter ON matter_participants(matter_id);
CREATE INDEX IF NOT EXISTS idx_matter_participants_user ON matter_participants(user_id);

CREATE TABLE IF NOT EXISTS matter_tags (
    matter_id       UUID NOT NULL REFERENCES matters(id) ON DELETE CASCADE,
    tag             TEXT NOT NULL,
    PRIMARY KEY (matter_id, tag)
);

CREATE TABLE IF NOT EXISTS matter_relationships (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_matter_id UUID NOT NULL REFERENCES matters(id) ON DELETE CASCADE,
    target_matter_id UUID NOT NULL REFERENCES matters(id) ON DELETE CASCADE,
    relationship    TEXT NOT NULL
                    CHECK (relationship IN (
                        'related', 'parent', 'child', 'consolidated', 'prior', 'subsequent'
                    )),
    notes           TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (source_matter_id != target_matter_id)
);

-- ---------------------------------------------------------------------------
-- 3.3 Evidence documents (files)
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS evidence_documents (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    matter_id       UUID NOT NULL REFERENCES matters(id) ON DELETE CASCADE,
    original_filename TEXT NOT NULL,
    file_extension  TEXT NOT NULL,
    mime_type       TEXT NOT NULL,
    file_size_bytes BIGINT NOT NULL,
    sha256_hash     TEXT NOT NULL,
    storage_bucket  TEXT NOT NULL,
    storage_key     TEXT NOT NULL,
    ingestion_status TEXT NOT NULL DEFAULT 'quarantine'
                    CHECK (ingestion_status IN (
                        'quarantine', 'scanning', 'validating', 'processing',
                        'classifying', 'privilege_screening', 'indexing',
                        'completed', 'failed', 'rejected'
                    )),
    ocr_status      TEXT NOT NULL DEFAULT 'pending'
                    CHECK (ocr_status IN (
                        'pending', 'in_progress', 'completed', 'failed', 'not_applicable'
                    )),
    ocr_confidence  NUMERIC(5,4),
    page_count      INTEGER,
    text_length     INTEGER,
    document_category TEXT
                    CHECK (document_category IS NULL OR document_category IN (
                        'correspondence', 'contract', 'notice', 'court_form',
                        'photo', 'financial_record', 'medical_record',
                        'government_letter', 'transcript', 'affidavit',
                        'regulation', 'case_law', 'policy_document',
                        'personal_note', 'other'
                    )),
    privilege_flag  TEXT NOT NULL DEFAULT 'unscreened'
                    CHECK (privilege_flag IN (
                        'unscreened', 'no_privilege',
                        'solicitor_client_privilege', 'litigation_privilege',
                        'without_prejudice', 'public_interest_privilege',
                        'privileged_review_required'
                    )),
    metadata_json   JSONB,
    source          TEXT
                    CHECK (source IS NULL OR source IN (
                        'upload', 'folder_connector', 'camera', 'email', 'scanner', 'api'
                    )),
    uploaded_by     UUID NOT NULL REFERENCES users(id),
    uploaded_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    processed_at    TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_evidence_docs_matter ON evidence_documents(matter_id);
CREATE INDEX IF NOT EXISTS idx_evidence_docs_status ON evidence_documents(ingestion_status);
CREATE INDEX IF NOT EXISTS idx_evidence_docs_hash ON evidence_documents(sha256_hash);
CREATE INDEX IF NOT EXISTS idx_evidence_docs_privilege ON evidence_documents(privilege_flag);

CREATE TABLE IF NOT EXISTS evidence_pages (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id     UUID NOT NULL REFERENCES evidence_documents(id) ON DELETE CASCADE,
    page_number     INTEGER NOT NULL,
    page_text       TEXT,
    text_confidence NUMERIC(5,4),
    page_hash       TEXT,
    is_blank        BOOLEAN NOT NULL DEFAULT false,
    has_images      BOOLEAN NOT NULL DEFAULT false,
    has_tables      BOOLEAN NOT NULL DEFAULT false,
    needs_review    BOOLEAN NOT NULL DEFAULT false,
    UNIQUE (document_id, page_number)
);

CREATE INDEX IF NOT EXISTS idx_evidence_pages_doc ON evidence_pages(document_id);

CREATE TABLE IF NOT EXISTS evidence_ocr_results (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id     UUID NOT NULL REFERENCES evidence_documents(id) ON DELETE CASCADE,
    page_id         UUID REFERENCES evidence_pages(id) ON DELETE CASCADE,
    engine          TEXT NOT NULL,
    engine_version  TEXT,
    raw_result_json JSONB,
    confidence      NUMERIC(5,4),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS evidence_extractions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id     UUID NOT NULL REFERENCES evidence_documents(id) ON DELETE CASCADE,
    page_id         UUID REFERENCES evidence_pages(id) ON DELETE SET NULL,
    extraction_type TEXT NOT NULL
                    CHECK (extraction_type IN (
                        'date', 'amount', 'name', 'address',
                        'phone', 'email', 'organization',
                        'clause', 'signature', 'seal',
                        'photo_subject', 'location'
                    )),
    extracted_value TEXT NOT NULL,
    confidence      NUMERIC(5,4),
    source_range    TEXT,
    metadata_json   JSONB,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_evidence_extractions_doc ON evidence_extractions(document_id);

CREATE TABLE IF NOT EXISTS evidence_classifications (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id     UUID NOT NULL REFERENCES evidence_documents(id) ON DELETE CASCADE,
    classification  TEXT NOT NULL,
    confidence      NUMERIC(5,4) NOT NULL,
    model_version   TEXT NOT NULL,
    reviewed_by     UUID REFERENCES users(id),
    reviewed_at     TIMESTAMPTZ,
    review_result   TEXT CHECK (review_result IS NULL OR review_result IN (
                        'accepted', 'rejected', 'modified'
                    )),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_evidence_class_doc ON evidence_classifications(document_id);

CREATE TABLE IF NOT EXISTS evidence_embeddings (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id     UUID NOT NULL REFERENCES evidence_documents(id) ON DELETE CASCADE,
    page_id         UUID REFERENCES evidence_pages(id) ON DELETE CASCADE,
    chunk_index     INTEGER NOT NULL,
    chunk_text      TEXT NOT NULL,
    embedding       vector(1536) NOT NULL,
    model_version   TEXT NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (document_id, chunk_index)
);

CREATE INDEX IF NOT EXISTS idx_evidence_embeddings_doc ON evidence_embeddings(document_id);

-- HNSW requires data; create index when table non-empty in ops:
-- CREATE INDEX idx_evidence_embeddings_vector ON evidence_embeddings
--   USING hnsw (embedding vector_cosine_ops);

CREATE TABLE IF NOT EXISTS evidence_privilege_screenings (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id     UUID NOT NULL REFERENCES evidence_documents(id) ON DELETE CASCADE,
    screening_model TEXT NOT NULL,
    screening_result TEXT NOT NULL
                    CHECK (screening_result IN (
                        'no_privilege_detected', 'possible_privilege',
                        'privilege_detected', 'inconclusive'
                    )),
    confidence      NUMERIC(5,4),
    rationale       TEXT,
    reviewed_by     UUID REFERENCES users(id),
    reviewed_at     TIMESTAMPTZ,
    review_result   TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_privilege_screenings_doc ON evidence_privilege_screenings(document_id);

CREATE TABLE IF NOT EXISTS evidence_chain_of_custody (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id     UUID NOT NULL REFERENCES evidence_documents(id) ON DELETE CASCADE,
    event_type      TEXT NOT NULL
                    CHECK (event_type IN (
                        'uploaded', 'transferred', 'viewed', 'exported',
                        'moved_storage', 'backed_up', 'deleted',
                        'hash_verified', 'access_granted', 'access_revoked'
                    )),
    actor_user_id   UUID REFERENCES users(id),
    actor_system    TEXT,
    from_location   TEXT,
    to_location     TEXT,
    notes           TEXT,
    occurred_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_chain_custody_doc ON evidence_chain_of_custody(document_id);

-- Timeline (depends on evidence_documents)
CREATE TABLE IF NOT EXISTS matter_timeline_entries (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    matter_id       UUID NOT NULL REFERENCES matters(id) ON DELETE CASCADE,
    entry_type      TEXT NOT NULL
                    CHECK (entry_type IN (
                        'event', 'filing', 'hearing', 'deadline',
                        'correspondence', 'evidence_ingested',
                        'document_drafted', 'status_change',
                        'research_note', 'system_note'
                    )),
    occurred_at     TIMESTAMPTZ NOT NULL,
    title           TEXT NOT NULL,
    description     TEXT,
    source_document_id UUID REFERENCES evidence_documents(id),
    is_confirmed    BOOLEAN NOT NULL DEFAULT false,
    created_by      UUID NOT NULL REFERENCES users(id),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_timeline_matter ON matter_timeline_entries(matter_id, occurred_at);

-- ---------------------------------------------------------------------------
-- 3.4 Evidence items (logical propositions / Evidence Matrix)
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS evidence_items (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    matter_id       UUID NOT NULL REFERENCES matters(id) ON DELETE CASCADE,
    proposition     TEXT NOT NULL,
    proposition_type TEXT NOT NULL
                    CHECK (proposition_type IN (
                        'fact', 'allegation', 'admission', 'assumption',
                        'inference', 'legal_argument', 'procedural_history',
                        'remedy', 'issue', 'authority', 'evidentiary_gap'
                    )),
    confidence      NUMERIC(5,4),
    dispute_status  TEXT NOT NULL DEFAULT 'unverified'
                    CHECK (dispute_status IN (
                        'unverified', 'verified', 'disputed', 'contradicted',
                        'retracted', 'confirmed_by_human'
                    )),
    issue_id        UUID REFERENCES evidence_items(id),
    created_by      UUID NOT NULL REFERENCES users(id),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_evidence_items_matter ON evidence_items(matter_id);
CREATE INDEX IF NOT EXISTS idx_evidence_items_type ON evidence_items(proposition_type);

CREATE TABLE IF NOT EXISTS evidence_item_links (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    evidence_item_id UUID NOT NULL REFERENCES evidence_items(id) ON DELETE CASCADE,
    document_id     UUID NOT NULL REFERENCES evidence_documents(id) ON DELETE CASCADE,
    page_id         UUID REFERENCES evidence_pages(id) ON DELETE SET NULL,
    page_number     INTEGER,
    paragraph_ref   TEXT,
    quote_text      TEXT,
    support_type    TEXT NOT NULL
                    CHECK (support_type IN (
                        'supports', 'contradicts', 'partially_supports',
                        'context', 'source_of', 'corroborates'
                    )),
    confidence      NUMERIC(5,4),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_evidence_links_item ON evidence_item_links(evidence_item_id);
CREATE INDEX IF NOT EXISTS idx_evidence_links_doc ON evidence_item_links(document_id);

CREATE TABLE IF NOT EXISTS evidence_item_relationships (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_item_id  UUID NOT NULL REFERENCES evidence_items(id) ON DELETE CASCADE,
    target_item_id  UUID NOT NULL REFERENCES evidence_items(id) ON DELETE CASCADE,
    relationship    TEXT NOT NULL
                    CHECK (relationship IN (
                        'supports', 'contradicts', 'corroborates',
                        'undermines', 'is_component_of', 'is_prerequisite_for',
                        'alternative_to', 'explains'
                    )),
    notes           TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (source_item_id != target_item_id)
);

CREATE INDEX IF NOT EXISTS idx_evidence_rel_source ON evidence_item_relationships(source_item_id);
CREATE INDEX IF NOT EXISTS idx_evidence_rel_target ON evidence_item_relationships(target_item_id);

-- ---------------------------------------------------------------------------
-- 3.5 Legal authorities & citation verification
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS legal_authorities (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    authority_type  TEXT NOT NULL
                    CHECK (authority_type IN (
                        'bc_statute', 'bc_regulation',
                        'federal_statute', 'federal_regulation',
                        'court_rule', 'tribunal_rule',
                        'rtb_policy_guideline', 'official_form',
                        'bc_sc_decision', 'bc_ca_decision', 'bc_pc_decision',
                        'scc_decision', 'tribunal_decision',
                        'other_jurisdiction_case'
                    )),
    full_citation   TEXT NOT NULL,
    short_title     TEXT,
    pin_cite        TEXT,
    source_url      TEXT,
    verified        BOOLEAN NOT NULL DEFAULT false,
    verified_at     TIMESTAMPTZ,
    verified_by     UUID REFERENCES users(id),
    verification_method TEXT
                    CHECK (verification_method IS NULL OR verification_method IN (
                        'official_source_check', 'automated_citation_check',
                        'human_review', 'cross_reference'
                    )),
    source_hash     TEXT,
    effective_from  DATE,
    effective_to    DATE,
    version_note    TEXT,
    court_level     TEXT
                    CHECK (court_level IS NULL OR court_level IN (
                        'supreme_court_of_canada', 'bc_court_of_appeal',
                        'bc_supreme_court', 'bc_provincial_court',
                        'tribunal', 'other'
                    )),
    binding_weight  TEXT
                    CHECK (binding_weight IS NULL OR binding_weight IN (
                        'binding', 'persuasive', 'distinguished',
                        'overruled', 'not_binding'
                    )),
    treatment       TEXT
                    CHECK (treatment IS NULL OR treatment IN (
                        'applied', 'followed', 'considered',
                        'distinguished', 'overruled', 'varied',
                        'not_followed', 'criticized', 'unknown'
                    )),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_authorities_type ON legal_authorities(authority_type);
CREATE INDEX IF NOT EXISTS idx_authorities_verified ON legal_authorities(verified);

CREATE TABLE IF NOT EXISTS authority_citations (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    authority_id    UUID NOT NULL REFERENCES legal_authorities(id) ON DELETE CASCADE,
    citing_authority_id UUID REFERENCES legal_authorities(id) ON DELETE SET NULL,
    matter_id       UUID REFERENCES matters(id) ON DELETE CASCADE,
    raw_citation    TEXT NOT NULL,
    context         TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS authority_pinpoints (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    authority_id    UUID NOT NULL REFERENCES legal_authorities(id) ON DELETE CASCADE,
    pinpoint        TEXT NOT NULL,
    proposition     TEXT,
    verified        BOOLEAN NOT NULL DEFAULT false,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS authority_treatment (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    authority_id    UUID NOT NULL REFERENCES legal_authorities(id) ON DELETE CASCADE,
    treating_authority_id UUID REFERENCES legal_authorities(id),
    treatment       TEXT NOT NULL
                    CHECK (treatment IN (
                        'applied', 'followed', 'considered', 'distinguished',
                        'overruled', 'varied', 'not_followed', 'criticized'
                    )),
    notes           TEXT,
    source_url      TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS authority_verification_results (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    authority_id    UUID NOT NULL REFERENCES legal_authorities(id) ON DELETE CASCADE,
    matter_id       UUID REFERENCES matters(id) ON DELETE SET NULL,
    status          TEXT NOT NULL
                    CHECK (status IN (
                        'UNVERIFIED', 'PROVISIONAL', 'VERIFIED', 'REJECTED', 'SUPERSEDED'
                    )),
    reasons         JSONB NOT NULL DEFAULT '[]'::jsonb,
    verified_by     UUID REFERENCES users(id),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS matter_authority_uses (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    matter_id       UUID NOT NULL REFERENCES matters(id) ON DELETE CASCADE,
    authority_id    UUID NOT NULL REFERENCES legal_authorities(id),
    use_context     TEXT NOT NULL DEFAULT '',
    court_ready_allowed BOOLEAN NOT NULL DEFAULT false,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (matter_id, authority_id)
);

-- ---------------------------------------------------------------------------
-- 3.6 Deadlines
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS deadlines (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    matter_id       UUID NOT NULL REFERENCES matters(id) ON DELETE CASCADE,
    label           TEXT NOT NULL,
    forum           TEXT,
    document_type   TEXT,
    service_method  TEXT,
    statutory_basis TEXT,
    state           TEXT NOT NULL DEFAULT 'UNASSESSED'
                    CHECK (state IN (
                        'UNASSESSED', 'POTENTIAL', 'CALCULATED',
                        'HUMAN_REVIEW_REQUIRED', 'HUMAN_CONFIRMED',
                        'DISPUTED', 'EXPIRED', 'EXTENSION_ANALYSIS_REQUIRED'
                    )),
    due_date        DATE,
    synthetic       BOOLEAN NOT NULL DEFAULT false,
    created_by      UUID REFERENCES users(id),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_deadlines_matter ON deadlines(matter_id);

CREATE TABLE IF NOT EXISTS deadline_calculations (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    deadline_id     UUID NOT NULL REFERENCES deadlines(id) ON DELETE CASCADE,
    start_date      DATE,
    window_days     INTEGER,
    assumptions     JSONB NOT NULL DEFAULT '[]'::jsonb,
    missing_inputs  JSONB NOT NULL DEFAULT '[]'::jsonb,
    calculated_due  DATE,
    engine_version  TEXT NOT NULL DEFAULT 'provisional_v1',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS deadline_confirmations (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    deadline_id     UUID NOT NULL REFERENCES deadlines(id) ON DELETE CASCADE,
    confirmed_by    UUID NOT NULL REFERENCES users(id),
    confirmed_due   DATE NOT NULL,
    notes           TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ---------------------------------------------------------------------------
-- 3.7 Draft documents
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS draft_documents (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    matter_id       UUID NOT NULL REFERENCES matters(id) ON DELETE CASCADE,
    form_number     TEXT,
    document_type   TEXT NOT NULL
                    CHECK (document_type IN (
                        'PETITION', 'RESPONSE_TO_PETITION', 'NOTICE_OF_APPLICATION',
                        'APPLICATION_RESPONSE', 'AFFIDAVIT', 'MEMORANDUM',
                        'CORRESPONDENCE', 'RTB_SUBMISSION', 'BOOK_OF_AUTHORITIES',
                        'BOOK_OF_DOCUMENTS', 'CHRONOLOGY', 'OTHER'
                    )),
    title           TEXT NOT NULL,
    court_ready     BOOLEAN NOT NULL DEFAULT false,
    status          TEXT NOT NULL DEFAULT 'draft'
                    CHECK (status IN (
                        'draft', 'in_review', 'approved', 'exported', 'superseded'
                    )),
    created_by      UUID NOT NULL REFERENCES users(id),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT form_66_petition CHECK (form_number IS DISTINCT FROM '66' OR document_type = 'PETITION'),
    CONSTRAINT form_67_response CHECK (form_number IS DISTINCT FROM '67' OR document_type = 'RESPONSE_TO_PETITION')
);

CREATE TABLE IF NOT EXISTS document_versions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    draft_id        UUID NOT NULL REFERENCES draft_documents(id) ON DELETE CASCADE,
    version_number  INTEGER NOT NULL,
    body_storage_key TEXT,
    body_hash       TEXT,
    change_summary  TEXT,
    created_by      UUID NOT NULL REFERENCES users(id),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (draft_id, version_number)
);

CREATE TABLE IF NOT EXISTS document_approvals (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    draft_id        UUID NOT NULL REFERENCES draft_documents(id) ON DELETE CASCADE,
    version_id      UUID REFERENCES document_versions(id),
    stage           TEXT NOT NULL
                    CHECK (stage IN ('REVIEW', 'APPROVE', 'PRIVILEGE', 'PROCEDURAL')),
    actor_id        UUID NOT NULL REFERENCES users(id),
    decision        TEXT NOT NULL
                    CHECK (decision IN ('approved', 'rejected', 'changes_requested')),
    notes           TEXT,
    snapshot_hash   TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS document_citation_links (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    draft_id        UUID NOT NULL REFERENCES draft_documents(id) ON DELETE CASCADE,
    authority_id    UUID NOT NULL REFERENCES legal_authorities(id),
    pin_cite        TEXT,
    location_hint   TEXT,
    verified        BOOLEAN NOT NULL DEFAULT false,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ---------------------------------------------------------------------------
-- 3.8 Communications
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS communications (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    matter_id       UUID NOT NULL REFERENCES matters(id) ON DELETE CASCADE,
    channel         TEXT NOT NULL
                    CHECK (channel IN (
                        'secure_message', 'email_draft', 'email_sent',
                        'sms_log', 'system_notice'
                    )),
    encryption_model TEXT
                    CHECK (encryption_model IS NULL OR encryption_model IN (
                        'MODEL_A_E2EE', 'MODEL_B_WORKSPACE'
                    )),
    subject         TEXT,
    body_preview    TEXT,
    body_storage_key TEXT,
    from_user_id    UUID REFERENCES users(id),
    to_participants JSONB NOT NULL DEFAULT '[]'::jsonb,
    send_status     TEXT NOT NULL DEFAULT 'draft'
                    CHECK (send_status IN (
                        'draft', 'pending_approval', 'sent', 'failed', 'blocked'
                    )),
    approved_by     UUID REFERENCES users(id),
    sent_at         TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT messaging_honesty CHECK (
        encryption_model IS NULL
        OR encryption_model != 'MODEL_A_E2EE'
        OR send_status = 'draft'
    )
);

CREATE TABLE IF NOT EXISTS communication_attachments (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    communication_id UUID NOT NULL REFERENCES communications(id) ON DELETE CASCADE,
    document_id     UUID REFERENCES evidence_documents(id),
    filename        TEXT NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS communication_privilege_flags (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    communication_id UUID NOT NULL REFERENCES communications(id) ON DELETE CASCADE,
    flag            TEXT NOT NULL
                    CHECK (flag IN (
                        'possible_privilege', 'client_confidential',
                        'without_prejudice', 'clear'
                    )),
    notes           TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ---------------------------------------------------------------------------
-- 3.9 Privilege & consent
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS privilege_records (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    matter_id       UUID NOT NULL REFERENCES matters(id) ON DELETE CASCADE,
    document_id     UUID REFERENCES evidence_documents(id),
    privilege_class TEXT NOT NULL
                    CHECK (privilege_class IN (
                        'solicitor_client', 'litigation', 'without_prejudice',
                        'common_interest', 'other'
                    )),
    description     TEXT,
    asserted_by     UUID NOT NULL REFERENCES users(id),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS privilege_releases (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    privilege_record_id UUID NOT NULL REFERENCES privilege_records(id) ON DELETE CASCADE,
    released_by     UUID NOT NULL REFERENCES users(id),
    scope           TEXT NOT NULL,
    recipient       TEXT,
    notes           TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS consent_records (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    matter_id       UUID NOT NULL REFERENCES matters(id) ON DELETE CASCADE,
    subject_user_id UUID REFERENCES users(id),
    subject_label   TEXT,
    category        TEXT NOT NULL
                    CHECK (category IN (
                        'AI_ANALYSIS', 'EXTERNAL_MODEL', 'DATA_SHARING',
                        'MARKETING', 'GENERAL', 'PRIVILEGE_PROCESSING'
                    )),
    purpose         TEXT NOT NULL,
    model_scope     TEXT NOT NULL DEFAULT 'PRIVATE_INFERENCE_ONLY'
                    CHECK (model_scope IN (
                        'NONE', 'PRIVATE_INFERENCE_ONLY', 'EXTERNAL_MODEL'
                    )),
    status          TEXT NOT NULL
                    CHECK (status IN (
                        'DRAFT', 'GRANTED', 'WITHDRAWN', 'EXPIRED', 'DENIED'
                    )),
    notice_version  TEXT NOT NULL,
    granted_at      TIMESTAMPTZ,
    withdrawn_at    TIMESTAMPTZ,
    expires_at      TIMESTAMPTZ,
    captured_by     UUID REFERENCES users(id),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (length(trim(purpose)) > 0)
);

CREATE INDEX IF NOT EXISTS idx_consent_matter ON consent_records(matter_id);

CREATE TABLE IF NOT EXISTS consent_audits (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    consent_id      UUID NOT NULL REFERENCES consent_records(id) ON DELETE CASCADE,
    action          TEXT NOT NULL,
    actor_id        UUID REFERENCES users(id),
    detail          JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ---------------------------------------------------------------------------
-- 3.10 Physical file management
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS physical_file_records (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    matter_id       UUID NOT NULL REFERENCES matters(id) ON DELETE CASCADE,
    label           TEXT NOT NULL,
    barcode         TEXT,
    box_id          TEXT,
    binder_id       TEXT,
    description     TEXT,
    linked_document_id UUID REFERENCES evidence_documents(id),
    retention_class TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS physical_file_locations (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    physical_file_id UUID NOT NULL REFERENCES physical_file_records(id) ON DELETE CASCADE,
    site            TEXT,
    room            TEXT,
    shelf           TEXT,
    notes           TEXT,
    effective_from  TIMESTAMPTZ NOT NULL DEFAULT now(),
    effective_to    TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS physical_file_movements (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    physical_file_id UUID NOT NULL REFERENCES physical_file_records(id) ON DELETE CASCADE,
    event_type      TEXT NOT NULL
                    CHECK (event_type IN (
                        'check_in', 'check_out', 'transfer', 'scan_queue',
                        'destruction', 'legal_hold'
                    )),
    actor_id        UUID REFERENCES users(id),
    from_location   TEXT,
    to_location     TEXT,
    notes           TEXT,
    occurred_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ---------------------------------------------------------------------------
-- 3.11 Conversations (workspace)
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS conversations (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_hint        TEXT,
    user_id         UUID NOT NULL REFERENCES users(id),
    title           TEXT NOT NULL DEFAULT 'New chat',
    chat_type       TEXT NOT NULL DEFAULT 'general'
                    CHECK (chat_type IN (
                        'general', 'matter', 'document', 'research',
                        'drafting', 'agent'
                    )),
    matter_id       UUID REFERENCES matters(id) ON DELETE SET NULL,
    model_mode      TEXT NOT NULL DEFAULT 'balanced',
    specialist      TEXT NOT NULL DEFAULT 'bc_legal_associate',
    archived        BOOLEAN NOT NULL DEFAULT false,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS chat_messages (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    role            TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system', 'tool')),
    content         TEXT NOT NULL,
    meta_json       JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_chat_messages_conv ON chat_messages(conversation_id, created_at);

-- ---------------------------------------------------------------------------
-- 3.12 Audit ledger (immutable)
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS audit_entries (
    seq             BIGSERIAL PRIMARY KEY,
    event_id        UUID NOT NULL UNIQUE DEFAULT gen_random_uuid(),
    matter_id       UUID,
    actor_user_id   UUID REFERENCES users(id),
    actor_system    TEXT,
    action          TEXT NOT NULL,
    resource_type   TEXT NOT NULL DEFAULT '',
    resource_id     TEXT NOT NULL DEFAULT '',
    detail          JSONB NOT NULL DEFAULT '{}'::jsonb,
    prev_hash       TEXT NOT NULL,
    entry_hash      TEXT NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_audit_matter ON audit_entries(matter_id, seq);
CREATE INDEX IF NOT EXISTS idx_audit_actor ON audit_entries(actor_user_id, seq);

-- ---------------------------------------------------------------------------
-- Seed roles
-- ---------------------------------------------------------------------------

INSERT INTO roles (name, description) VALUES
  ('system_admin', 'System administrator'),
  ('lawyer', 'Licensed lawyer'),
  ('articled_student', 'Articled student'),
  ('paralegal', 'Paralegal'),
  ('client', 'Client participant'),
  ('self_represented', 'Self-represented litigant'),
  ('expert', 'Expert witness'),
  ('witness', 'Factual witness'),
  ('auditor', 'Read-only auditor')
ON CONFLICT (name) DO NOTHING;

-- ---------------------------------------------------------------------------
-- RLS helpers (enable after app sets: SET app.current_user_id = '...')
-- ---------------------------------------------------------------------------

-- Example policy pattern (commented until session GUC is set by app):
-- ALTER TABLE evidence_documents ENABLE ROW LEVEL SECURITY;
-- CREATE POLICY evidence_docs_participant ON evidence_documents
--   FOR ALL USING (
--     matter_id IN (
--       SELECT matter_id FROM matter_participants
--       WHERE user_id = current_setting('app.current_user_id', true)::uuid
--         AND active = true AND access_level <> 'no_access'
--         AND (left_at IS NULL OR left_at > now())
--     )
--   );

COMMIT;
