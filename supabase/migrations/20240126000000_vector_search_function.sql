-- Vector Search Function
-- 
-- Creates a Postgres function for efficient vector similarity search using pgvector.
-- This function uses the cosine distance operator (<=>) for fast similarity search.

CREATE OR REPLACE FUNCTION search_similar_chunks(
  query_embedding vector(1536),
  p_app_id uuid,
  p_top_k integer DEFAULT 5,
  p_similarity_threshold float DEFAULT 0.0,
  p_email_id uuid DEFAULT NULL,
  p_attachment_id uuid DEFAULT NULL
)
RETURNS TABLE (
  chunk_id uuid,
  content text,
  similarity float,
  chunk_index integer,
  email_id uuid,
  attachment_id uuid,
  metadata jsonb
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT
    dc.id AS chunk_id,
    dc.content,
    1 - (dc.embedding <=> query_embedding) AS similarity,
    dc.chunk_index,
    dc.email_id,
    dc.attachment_id,
    dc.metadata
  FROM document_chunks dc
  WHERE
    dc.app_id = p_app_id
    AND dc.status = 'completed'
    AND dc.embedding IS NOT NULL
    AND (p_email_id IS NULL OR dc.email_id = p_email_id)
    AND (p_attachment_id IS NULL OR dc.attachment_id = p_attachment_id)
    AND (1 - (dc.embedding <=> query_embedding)) >= p_similarity_threshold
  ORDER BY dc.embedding <=> query_embedding
  LIMIT p_top_k;
END;
$$;

-- Create index for better performance (if not already exists)
-- The HNSW index should already exist from the initial schema migration
-- CREATE INDEX IF NOT EXISTS idx_document_chunks_embedding 
--   ON document_chunks USING hnsw (embedding vector_cosine_ops);

-- Grant execute permission
GRANT EXECUTE ON FUNCTION search_similar_chunks TO authenticated;
GRANT EXECUTE ON FUNCTION search_similar_chunks TO service_role;
