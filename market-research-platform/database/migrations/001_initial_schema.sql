-- filepath: market-research-platform/database/migrations/001_initial_schema.sql
-- Initial schema migration. Documents the full application table structure.
-- This file is for reference / Alembic migration use in Phase 3+.
-- For the POC, tables are auto-created by SQLAlchemy (see database.py init_db).

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS vector;

-- ── documents ────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS documents (
    id                  SERIAL PRIMARY KEY,
    title               VARCHAR(512)    NOT NULL,
    source_type         VARCHAR(50)     NOT NULL CHECK (source_type IN ('pdf_upload', 'news_article')),
    source_name         VARCHAR(256),
    original_url        TEXT,
    file_path           TEXT,
    ingested_at         TIMESTAMP       NOT NULL DEFAULT NOW(),
    metadata            JSONB           DEFAULT '{}',
    llamaindex_doc_id   VARCHAR(256),
    -- TODO: indexing_status VARCHAR(50) DEFAULT 'pending'
    CONSTRAINT documents_source_check CHECK (
        (source_type = 'pdf_upload'    AND file_path IS NOT NULL) OR
        (source_type = 'news_article'  AND original_url IS NOT NULL)
    )
);

CREATE INDEX IF NOT EXISTS idx_documents_source_type  ON documents (source_type);
CREATE INDEX IF NOT EXISTS idx_documents_ingested_at  ON documents (ingested_at DESC);
-- TODO: CREATE INDEX idx_documents_metadata ON documents USING gin (metadata);

-- ── reports ──────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS reports (
    id                      SERIAL PRIMARY KEY,
    title                   VARCHAR(512)    NOT NULL,
    report_type             VARCHAR(50)     NOT NULL CHECK (report_type IN ('executive_summary', 'trend_report', 'custom')),
    content                 TEXT,
    generated_at            TIMESTAMP       NOT NULL DEFAULT NOW(),
    is_scheduled            BOOLEAN         DEFAULT FALSE,
    schedule_config         JSONB           DEFAULT NULL,
    source_document_ids     JSONB           DEFAULT '[]'
    -- TODO: status VARCHAR(50) DEFAULT 'complete'
);

CREATE INDEX IF NOT EXISTS idx_reports_generated_at ON reports (generated_at DESC);
CREATE INDEX IF NOT EXISTS idx_reports_type         ON reports (report_type);

-- ── chat_sessions ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS chat_sessions (
    id          SERIAL PRIMARY KEY,
    started_at  TIMESTAMP   NOT NULL DEFAULT NOW(),
    messages    JSONB       DEFAULT '[]'
    -- TODO: ended_at TIMESTAMP
);

-- ── trends ────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS trends (
    id                      SERIAL PRIMARY KEY,
    title                   VARCHAR(512)    NOT NULL,
    description             TEXT,
    confidence_score        FLOAT           CHECK (confidence_score BETWEEN 0.0 AND 1.0),
    supporting_chunk_ids    JSONB           DEFAULT '[]',
    source_document_ids     JSONB           DEFAULT '[]',
    identified_at           TIMESTAMP       NOT NULL DEFAULT NOW(),
    tags                    JSONB           DEFAULT '[]'
    -- TODO: is_active BOOLEAN DEFAULT TRUE
    -- TODO: industry_vertical VARCHAR(128)
);

CREATE INDEX IF NOT EXISTS idx_trends_identified_at      ON trends (identified_at DESC);
CREATE INDEX IF NOT EXISTS idx_trends_confidence_score   ON trends (confidence_score DESC);
