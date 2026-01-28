-- Performance Indexes Migration
-- 
-- Adds additional indexes for optimal query performance, especially for:
-- 1. Vector search queries (app_id + embedding filtering)
-- 2. Multi-tenant queries (app_id filtering)
-- 3. Whitelist lookups (app_id + email_address)
-- 4. Common query patterns

-- ============================================================================
-- DOCUMENT_CHUNKS INDEXES (Critical for Vector Search Performance)
-- ============================================================================

-- Note: Composite index with vector column is not supported in PostgreSQL
-- PostgreSQL will efficiently use the existing separate indexes:
-- - idx_document_chunks_app_id (B-tree on app_id)
-- - idx_document_chunks_embedding (HNSW on embedding)
-- The query planner will combine these indexes automatically

-- Index on status for filtering completed chunks (if status column exists)
-- Note: Check if status column exists in document_chunks table
-- If not, this index creation will be skipped
DO $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM information_schema.columns 
    WHERE table_name = 'document_chunks' AND column_name = 'status'
  ) THEN
    CREATE INDEX IF NOT EXISTS idx_document_chunks_status 
      ON document_chunks(status) 
      WHERE status = 'completed';
    
    -- Composite index for app_id + status (common filter pattern)
    CREATE INDEX IF NOT EXISTS idx_document_chunks_app_id_status 
      ON document_chunks(app_id, status) 
      WHERE status = 'completed';
  END IF;
END $$;

-- Index on chunk_index for ordering within documents
CREATE INDEX IF NOT EXISTS idx_document_chunks_chunk_index 
  ON document_chunks(chunk_index);

-- Composite index for app_id + email_id lookups
CREATE INDEX IF NOT EXISTS idx_document_chunks_app_id_email_id 
  ON document_chunks(app_id, email_id);

-- Composite index for app_id + attachment_id lookups
CREATE INDEX IF NOT EXISTS idx_document_chunks_app_id_attachment_id 
  ON document_chunks(app_id, attachment_id) 
  WHERE attachment_id IS NOT NULL;

-- GIN index on metadata JSONB for efficient JSON queries
CREATE INDEX IF NOT EXISTS idx_document_chunks_metadata_gin 
  ON document_chunks USING gin(metadata);

-- ============================================================================
-- WHITELIST INDEXES (Critical for Email Routing Performance)
-- ============================================================================

-- Composite index for fast whitelist lookups (app_id + email_address)
-- This is the most common query pattern: "Is this email whitelisted for this app?"
CREATE INDEX IF NOT EXISTS idx_sender_whitelist_app_id_email 
  ON sender_whitelist(app_id, email_address);

-- Composite index with enabled filter for active whitelist lookups
CREATE INDEX IF NOT EXISTS idx_sender_whitelist_app_id_email_enabled 
  ON sender_whitelist(app_id, email_address) 
  WHERE enabled = TRUE;

-- Same for query whitelist
CREATE INDEX IF NOT EXISTS idx_query_whitelist_app_id_email 
  ON query_whitelist(app_id, email_address);

-- Composite index with enabled filter for active query whitelist lookups
CREATE INDEX IF NOT EXISTS idx_query_whitelist_app_id_email_enabled 
  ON query_whitelist(app_id, email_address) 
  WHERE enabled = TRUE;

-- ============================================================================
-- EMAIL QUERIES INDEXES (For Query History Performance)
-- ============================================================================

-- Composite index for app_id + sender_email lookups
CREATE INDEX IF NOT EXISTS idx_email_queries_app_id_sender 
  ON email_queries(app_id, sender_email);

-- Composite index for app_id + thread_id lookups
CREATE INDEX IF NOT EXISTS idx_email_queries_app_id_thread 
  ON email_queries(app_id, thread_id) 
  WHERE thread_id IS NOT NULL;

-- ============================================================================
-- QUERY THREADS INDEXES (For Thread Lookups)
-- ============================================================================

-- Composite index for app_id + thread_id lookups (already has UNIQUE, but index helps)
CREATE INDEX IF NOT EXISTS idx_query_threads_app_id_thread 
  ON query_threads(app_id, thread_id);

-- Composite index for app_id + sender_email lookups
CREATE INDEX IF NOT EXISTS idx_query_threads_app_id_sender 
  ON query_threads(app_id, sender_email);

-- ============================================================================
-- PROCESSING LOGS INDEXES (For Monitoring and Debugging)
-- ============================================================================

-- Index on function_name for filtering by processing function
CREATE INDEX IF NOT EXISTS idx_processing_logs_function_name 
  ON processing_logs(function_name) 
  WHERE function_name IS NOT NULL;

-- Index on status for filtering by processing status
CREATE INDEX IF NOT EXISTS idx_processing_logs_status 
  ON processing_logs(status) 
  WHERE status IS NOT NULL;

-- Composite index for app_id + function_name lookups
CREATE INDEX IF NOT EXISTS idx_processing_logs_app_id_function 
  ON processing_logs(app_id, function_name) 
  WHERE function_name IS NOT NULL;

-- Composite index for app_id + status lookups
CREATE INDEX IF NOT EXISTS idx_processing_logs_app_id_status 
  ON processing_logs(app_id, status) 
  WHERE status IS NOT NULL;

-- ============================================================================
-- EMAILS INDEXES (Additional Performance Indexes)
-- ============================================================================

-- Composite index for app_id + sender_email lookups
CREATE INDEX IF NOT EXISTS idx_emails_app_id_sender 
  ON emails(app_id, sender_email);

-- Composite index for app_id + received_at (for date range queries)
CREATE INDEX IF NOT EXISTS idx_emails_app_id_received_at 
  ON emails(app_id, received_at DESC);

-- Index on processed_at for tracking processing status
CREATE INDEX IF NOT EXISTS idx_emails_processed_at 
  ON emails(processed_at) 
  WHERE processed_at IS NOT NULL;

-- ============================================================================
-- ATTACHMENTS INDEXES (Additional Performance Indexes)
-- ============================================================================

-- Composite index for app_id + email_id lookups
CREATE INDEX IF NOT EXISTS idx_attachments_app_id_email_id 
  ON attachments(app_id, email_id);

-- Index on processed_at for tracking attachment processing
CREATE INDEX IF NOT EXISTS idx_attachments_processed_at 
  ON attachments(processed_at) 
  WHERE processed_at IS NOT NULL;

-- ============================================================================
-- APP_MEMBERS INDEXES (For User-App Lookups)
-- ============================================================================

-- Composite index for user_id + role lookups (for permission checks)
CREATE INDEX IF NOT EXISTS idx_app_members_user_id_role 
  ON app_members(user_id, role);

-- Index on role for role-based queries
CREATE INDEX IF NOT EXISTS idx_app_members_role 
  ON app_members(role);

-- ============================================================================
-- ANALYZE TABLES (Update Statistics for Query Planner)
-- ============================================================================

-- Update table statistics for better query planning
ANALYZE apps;
ANALYZE app_members;
ANALYZE emails;
ANALYZE attachments;
ANALYZE document_chunks;
ANALYZE processing_logs;
ANALYZE sender_whitelist;
ANALYZE query_whitelist;
ANALYZE email_queries;
ANALYZE query_threads;
