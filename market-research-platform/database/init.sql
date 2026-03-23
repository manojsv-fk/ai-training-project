-- filepath: market-research-platform/database/init.sql
-- Database initialization script. Run automatically by the PostgreSQL Docker container
-- on first startup via the docker-entrypoint-initdb.d/ mount.
-- Creates the pgvector extension required by LlamaIndex PGVectorStore.

-- Enable pgvector extension (required for embedding storage)
CREATE EXTENSION IF NOT EXISTS vector;

-- Note: Application tables (documents, reports, chat_sessions, trends) are created
-- by SQLAlchemy's init_db() on backend startup (Base.metadata.create_all).
-- This script only handles DB-level setup that SQLAlchemy cannot do.

-- TODO: In production, replace SQLAlchemy auto-create with Alembic migrations.
-- TODO: Add any PostgreSQL-specific indexes on JSONB fields here if needed.
-- TODO: Add pg_trgm extension if full-text search on document titles is desired:
--   CREATE EXTENSION IF NOT EXISTS pg_trgm;
