-- My Building Board - Initial Database Schema
-- Multi-tenant email-to-QA system with RAG

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";

-- ============================================================================
-- MULTI-TENANT TABLES
-- ============================================================================

-- Apps table: Building boards (tenants/organizations)
CREATE TABLE apps (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  name TEXT NOT NULL,
  subdomain TEXT UNIQUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CONSTRAINT apps_name_length CHECK (char_length(name) >= 1 AND char_length(name) <= 255),
  CONSTRAINT apps_subdomain_format CHECK (subdomain IS NULL OR (subdomain ~ '^[a-z0-9-]+$' AND char_length(subdomain) >= 3 AND char_length(subdomain) <= 63))
);

-- App members: User-organization relationships with roles
CREATE TABLE app_members (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  app_id UUID NOT NULL REFERENCES apps(id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  role TEXT NOT NULL CHECK (role IN ('owner', 'admin', 'member')),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE(app_id, user_id),
  CONSTRAINT app_members_role_valid CHECK (role IN ('owner', 'admin', 'member'))
);

-- App configs: App-specific configurations (optional, for future customization)
CREATE TABLE app_configs (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  app_id UUID NOT NULL REFERENCES apps(id) ON DELETE CASCADE UNIQUE,
  config JSONB NOT NULL DEFAULT '{}',
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================================
-- TENANT-SCOPED TABLES (All include app_id for isolation)
-- ============================================================================

-- Emails: Ingested emails from email providers
CREATE TABLE emails (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  app_id UUID NOT NULL REFERENCES apps(id) ON DELETE CASCADE,
  provider_id TEXT NOT NULL,
  provider_type TEXT NOT NULL CHECK (provider_type IN ('gmail', 'imap', 'sendgrid', 'mailgun', 'microsoft_graph')),
  thread_id TEXT,
  sender_email TEXT NOT NULL,
  sender_name TEXT,
  subject TEXT,
  body_text TEXT,
  body_html TEXT,
  received_at TIMESTAMPTZ NOT NULL,
  processed_at TIMESTAMPTZ,
  status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
  provider_metadata JSONB NOT NULL DEFAULT '{}',
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE(app_id, provider_id, provider_type),
  CONSTRAINT emails_sender_email_format CHECK (sender_email ~ '^[^@]+@[^@]+\.[^@]+$')
);

-- Attachments: Email attachments (PDFs, DOCX, images, etc.)
CREATE TABLE attachments (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  app_id UUID NOT NULL REFERENCES apps(id) ON DELETE CASCADE,
  email_id UUID REFERENCES emails(id) ON DELETE CASCADE,
  provider_attachment_id TEXT,
  filename TEXT NOT NULL,
  content_type TEXT,
  file_size BIGINT,
  storage_path TEXT,
  extracted_text TEXT,
  chunk_count INTEGER NOT NULL DEFAULT 0,
  processed_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CONSTRAINT attachments_file_size_positive CHECK (file_size IS NULL OR file_size >= 0),
  CONSTRAINT attachments_chunk_count_positive CHECK (chunk_count >= 0)
);

-- Document chunks: Text chunks with vector embeddings for semantic search
CREATE TABLE document_chunks (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  app_id UUID NOT NULL REFERENCES apps(id) ON DELETE CASCADE,
  email_id UUID NOT NULL REFERENCES emails(id) ON DELETE CASCADE,
  attachment_id UUID REFERENCES attachments(id) ON DELETE SET NULL,
  chunk_index INTEGER NOT NULL,
  content TEXT NOT NULL,
  embedding vector(1536),
  token_count INTEGER,
  metadata JSONB NOT NULL DEFAULT '{}',
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CONSTRAINT document_chunks_chunk_index_positive CHECK (chunk_index >= 0),
  CONSTRAINT document_chunks_token_count_positive CHECK (token_count IS NULL OR token_count >= 0)
);

-- Processing logs: Track processing steps for debugging and monitoring
CREATE TABLE processing_logs (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  app_id UUID NOT NULL REFERENCES apps(id) ON DELETE CASCADE,
  email_id UUID REFERENCES emails(id) ON DELETE CASCADE,
  function_name TEXT,
  status TEXT CHECK (status IN ('success', 'failed', 'skipped')),
  error_message TEXT,
  processing_time_ms INTEGER,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CONSTRAINT processing_logs_processing_time_positive CHECK (processing_time_ms IS NULL OR processing_time_ms >= 0)
);

-- Sender whitelist: Control who can send documents (per app)
CREATE TABLE sender_whitelist (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  app_id UUID NOT NULL REFERENCES apps(id) ON DELETE CASCADE,
  email_address TEXT NOT NULL,
  enabled BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE(app_id, email_address),
  CONSTRAINT sender_whitelist_email_format CHECK (email_address ~ '^[^@]+@[^@]+\.[^@]+$')
);

-- Query whitelist: Control who can ask questions via email (per app)
CREATE TABLE query_whitelist (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  app_id UUID NOT NULL REFERENCES apps(id) ON DELETE CASCADE,
  email_address TEXT NOT NULL,
  enabled BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE(app_id, email_address),
  CONSTRAINT query_whitelist_email_format CHECK (email_address ~ '^[^@]+@[^@]+\.[^@]+$')
);

-- Email queries: Questions asked via email
CREATE TABLE email_queries (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  app_id UUID NOT NULL REFERENCES apps(id) ON DELETE CASCADE,
  sender_email TEXT NOT NULL,
  query_text TEXT NOT NULL,
  answer_text TEXT,
  thread_id TEXT,
  sources_used JSONB,
  status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  answered_at TIMESTAMPTZ,
  CONSTRAINT email_queries_sender_email_format CHECK (sender_email ~ '^[^@]+@[^@]+\.[^@]+$')
);

-- Query threads: Conversation threads for follow-up questions
CREATE TABLE query_threads (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  app_id UUID NOT NULL REFERENCES apps(id) ON DELETE CASCADE,
  thread_id TEXT NOT NULL,
  sender_email TEXT NOT NULL,
  conversation_history JSONB NOT NULL DEFAULT '[]',
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE(app_id, thread_id),
  CONSTRAINT query_threads_sender_email_format CHECK (sender_email ~ '^[^@]+@[^@]+\.[^@]+$')
);

-- ============================================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================================

-- Apps indexes
CREATE INDEX idx_apps_subdomain ON apps(subdomain) WHERE subdomain IS NOT NULL;

-- App members indexes
CREATE INDEX idx_app_members_app_id ON app_members(app_id);
CREATE INDEX idx_app_members_user_id ON app_members(user_id);
CREATE INDEX idx_app_members_app_user ON app_members(app_id, user_id);

-- Emails indexes
CREATE INDEX idx_emails_app_id ON emails(app_id);
CREATE INDEX idx_emails_app_id_status ON emails(app_id, status);
CREATE INDEX idx_emails_provider ON emails(provider_type, provider_id);
CREATE INDEX idx_emails_received_at ON emails(received_at DESC);
CREATE INDEX idx_emails_thread_id ON emails(thread_id) WHERE thread_id IS NOT NULL;

-- Attachments indexes
CREATE INDEX idx_attachments_app_id ON attachments(app_id);
CREATE INDEX idx_attachments_email_id ON attachments(email_id);

-- Document chunks indexes
CREATE INDEX idx_document_chunks_app_id ON document_chunks(app_id);
CREATE INDEX idx_document_chunks_email_id ON document_chunks(email_id);
CREATE INDEX idx_document_chunks_attachment_id ON document_chunks(attachment_id) WHERE attachment_id IS NOT NULL;
-- Vector similarity search index (HNSW for fast approximate nearest neighbor search)
CREATE INDEX idx_document_chunks_embedding ON document_chunks USING hnsw (embedding vector_cosine_ops);

-- Processing logs indexes
CREATE INDEX idx_processing_logs_app_id ON processing_logs(app_id);
CREATE INDEX idx_processing_logs_email_id ON processing_logs(email_id);
CREATE INDEX idx_processing_logs_created_at ON processing_logs(created_at DESC);

-- Whitelist indexes
CREATE INDEX idx_sender_whitelist_app_id ON sender_whitelist(app_id);
CREATE INDEX idx_sender_whitelist_email ON sender_whitelist(email_address);
CREATE INDEX idx_query_whitelist_app_id ON query_whitelist(app_id);
CREATE INDEX idx_query_whitelist_email ON query_whitelist(email_address);

-- Email queries indexes
CREATE INDEX idx_email_queries_app_id ON email_queries(app_id);
CREATE INDEX idx_email_queries_app_id_status ON email_queries(app_id, status);
CREATE INDEX idx_email_queries_sender_email ON email_queries(sender_email);
CREATE INDEX idx_email_queries_thread_id ON email_queries(thread_id) WHERE thread_id IS NOT NULL;
CREATE INDEX idx_email_queries_created_at ON email_queries(created_at DESC);

-- Query threads indexes
CREATE INDEX idx_query_threads_app_id ON query_threads(app_id);
CREATE INDEX idx_query_threads_sender_email ON query_threads(sender_email);

-- ============================================================================
-- ROW LEVEL SECURITY (RLS) POLICIES
-- ============================================================================

-- Enable RLS on all tables
ALTER TABLE apps ENABLE ROW LEVEL SECURITY;
ALTER TABLE app_members ENABLE ROW LEVEL SECURITY;
ALTER TABLE app_configs ENABLE ROW LEVEL SECURITY;
ALTER TABLE emails ENABLE ROW LEVEL SECURITY;
ALTER TABLE attachments ENABLE ROW LEVEL SECURITY;
ALTER TABLE document_chunks ENABLE ROW LEVEL SECURITY;
ALTER TABLE processing_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE sender_whitelist ENABLE ROW LEVEL SECURITY;
ALTER TABLE query_whitelist ENABLE ROW LEVEL SECURITY;
ALTER TABLE email_queries ENABLE ROW LEVEL SECURITY;
ALTER TABLE query_threads ENABLE ROW LEVEL SECURITY;

-- Apps: Users can read apps they're members of
CREATE POLICY "Users can read apps they're members of"
  ON apps FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM app_members
      WHERE app_members.app_id = apps.id
      AND app_members.user_id = auth.uid()
    )
  );

-- App members: Users can read their own memberships
CREATE POLICY "Users can read their own memberships"
  ON app_members FOR SELECT
  USING (user_id = auth.uid());

-- App configs: Users can read configs for apps they're members of
CREATE POLICY "Users can read app configs for their apps"
  ON app_configs FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM app_members
      WHERE app_members.app_id = app_configs.app_id
      AND app_members.user_id = auth.uid()
    )
  );

-- Emails: Users can read emails for apps they're members of
CREATE POLICY "Users can read emails for their apps"
  ON emails FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM app_members
      WHERE app_members.app_id = emails.app_id
      AND app_members.user_id = auth.uid()
    )
  );

-- Attachments: Users can read attachments for apps they're members of
CREATE POLICY "Users can read attachments for their apps"
  ON attachments FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM app_members
      WHERE app_members.app_id = attachments.app_id
      AND app_members.user_id = auth.uid()
    )
  );

-- Document chunks: Users can read chunks for apps they're members of
CREATE POLICY "Users can read chunks for their apps"
  ON document_chunks FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM app_members
      WHERE app_members.app_id = document_chunks.app_id
      AND app_members.user_id = auth.uid()
    )
  );

-- Processing logs: Users can read logs for apps they're members of
CREATE POLICY "Users can read logs for their apps"
  ON processing_logs FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM app_members
      WHERE app_members.app_id = processing_logs.app_id
      AND app_members.user_id = auth.uid()
    )
  );

-- Sender whitelist: Users can read/manage whitelist for apps they're admins/owners of
CREATE POLICY "Admins can manage sender whitelist"
  ON sender_whitelist FOR ALL
  USING (
    EXISTS (
      SELECT 1 FROM app_members
      WHERE app_members.app_id = sender_whitelist.app_id
      AND app_members.user_id = auth.uid()
      AND app_members.role IN ('owner', 'admin')
    )
  );

-- Query whitelist: Users can read/manage whitelist for apps they're admins/owners of
CREATE POLICY "Admins can manage query whitelist"
  ON query_whitelist FOR ALL
  USING (
    EXISTS (
      SELECT 1 FROM app_members
      WHERE app_members.app_id = query_whitelist.app_id
      AND app_members.user_id = auth.uid()
      AND app_members.role IN ('owner', 'admin')
    )
  );

-- Email queries: Users can read queries for apps they're members of
CREATE POLICY "Users can read queries for their apps"
  ON email_queries FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM app_members
      WHERE app_members.app_id = email_queries.app_id
      AND app_members.user_id = auth.uid()
    )
  );

-- Query threads: Users can read threads for apps they're members of
CREATE POLICY "Users can read threads for their apps"
  ON query_threads FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM app_members
      WHERE app_members.app_id = query_threads.app_id
      AND app_members.user_id = auth.uid()
    )
  );

-- ============================================================================
-- FUNCTIONS AND TRIGGERS
-- ============================================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers for updated_at
CREATE TRIGGER update_apps_updated_at
  BEFORE UPDATE ON apps
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_app_members_updated_at
  BEFORE UPDATE ON app_members
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_app_configs_updated_at
  BEFORE UPDATE ON app_configs
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_emails_updated_at
  BEFORE UPDATE ON emails
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_query_threads_updated_at
  BEFORE UPDATE ON query_threads
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();
