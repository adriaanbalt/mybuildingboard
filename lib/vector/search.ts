/**
 * Vector Search Service
 * 
 * Provides vector similarity search using pgvector in Supabase.
 */

import { createServerSupabaseClient } from '@/lib/auth/server';
import type { SearchResult, VectorSearchOptions } from './types';

/**
 * Search for similar chunks using vector similarity.
 * 
 * Uses pgvector cosine similarity to find the most similar document chunks.
 * 
 * @param queryEmbedding - Query embedding vector (1536 dimensions for text-embedding-3-small)
 * @param options - Search options including app_id, top_k, filters, etc.
 * @returns Array of search results sorted by similarity (descending)
 */
export async function searchSimilarChunks(
  queryEmbedding: number[],
  options: VectorSearchOptions
): Promise<SearchResult[]> {
  const supabase = await createServerSupabaseClient();
  
  // Validate embedding dimensions
  if (queryEmbedding.length !== 1536) {
    throw new Error(`Invalid embedding dimensions: expected 1536, got ${queryEmbedding.length}`);
  }
  
  // Validate app_id is provided
  if (!options.appId) {
    throw new Error('app_id is required for vector search');
  }
  
  const topK = options.topK || 5;
  const similarityThreshold = options.similarityThreshold ?? 0.0;
  
  // Convert embedding to pgvector format: '[0.1,0.2,0.3,...]'
  const embeddingStr = '[' + queryEmbedding.join(',') + ']';
  
  // Use Postgres RPC function for efficient vector similarity search
  const { data, error } = await supabase.rpc('search_similar_chunks', {
    query_embedding: embeddingStr,
    p_app_id: options.appId,
    p_top_k: topK,
    p_similarity_threshold: similarityThreshold,
    p_email_id: options.emailId || null,
    p_attachment_id: options.attachmentId || null,
  });
  
  if (error) {
    throw new Error(`Vector search failed: ${error.message}`);
  }
  
  if (!data || data.length === 0) {
    return [];
  }
  
  // Get email and attachment details for results
  interface ChunkResult {
    email_id: string;
    attachment_id: string | null;
    chunk_id: string;
    content: string;
    similarity: number;
    chunk_index: number;
    metadata: Record<string, unknown> | null;
  }
  
  interface EmailResult {
    id: string;
    subject: string;
    sender_email: string;
  }
  
  interface AttachmentResult {
    id: string;
    filename: string;
    content_type: string;
  }
  
  const emailIds = [...new Set((data as ChunkResult[]).map((chunk) => chunk.email_id))];
  const attachmentIds = (data as ChunkResult[])
    .map((chunk) => chunk.attachment_id)
    .filter((id: string | null): id is string => id !== null);
  
  const [emailsResult, attachmentsResult] = await Promise.all([
    emailIds.length > 0
      ? supabase.from('emails').select('id, subject, sender_email').in('id', emailIds)
      : Promise.resolve({ data: [], error: null }),
    attachmentIds.length > 0
      ? supabase.from('attachments').select('id, filename, content_type').in('id', attachmentIds)
      : Promise.resolve({ data: [], error: null }),
  ]);
  
  const emails = new Map((emailsResult.data || []).map((e: EmailResult) => [e.id, e]));
  const attachments = new Map((attachmentsResult.data || []).map((a: AttachmentResult) => [a.id, a]));
  
  // Process results (similarity already calculated by Postgres function)
  const results: SearchResult[] = (data as ChunkResult[]).map((chunk) => {
    const email = emails.get(chunk.email_id);
    const attachment = chunk.attachment_id ? attachments.get(chunk.attachment_id) : null;
    
    return {
      chunkId: chunk.chunk_id,
      content: chunk.content,
      similarity: chunk.similarity,
      metadata: {
        emailId: chunk.email_id,
        attachmentId: chunk.attachment_id,
        chunkIndex: chunk.chunk_index,
        appId: options.appId,
        ...(chunk.metadata || {}),
      },
      source: {
        emailId: chunk.email_id,
        emailSubject: email?.subject,
        attachmentId: chunk.attachment_id || undefined,
        attachmentFilename: attachment?.filename,
      },
    };
  });
  
  return results;
}

/**
 * Calculate cosine similarity between two vectors.
 * 
 * @param vec1 - First vector
 * @param vec2 - Second vector
 * @returns Cosine similarity score (0-1)
 */
function _calculateCosineSimilarity(vec1: number[], vec2: number[]): number {
  if (vec1.length !== vec2.length) {
    throw new Error('Vectors must have the same length');
  }
  
  let dotProduct = 0;
  let norm1 = 0;
  let norm2 = 0;
  
  for (let i = 0; i < vec1.length; i++) {
    dotProduct += vec1[i] * vec2[i];
    norm1 += vec1[i] * vec1[i];
    norm2 += vec2[i] * vec2[i];
  }
  
  const magnitude = Math.sqrt(norm1) * Math.sqrt(norm2);
  
  if (magnitude === 0) {
    return 0;
  }
  
  return dotProduct / magnitude;
}

/**
 * Parse embedding vector from database format.
 * 
 * @param embedding - Embedding from database (string or array)
 * @returns Array of numbers
 */
function _parseEmbeddingVector(embedding: string | number[] | null): number[] {
  if (!embedding) {
    throw new Error('Embedding is null or undefined');
  }
  
  if (Array.isArray(embedding)) {
    return embedding;
  }
  
  if (typeof embedding === 'string') {
    // Parse pgvector format: '[0.1,0.2,0.3,...]'
    const cleaned = embedding.replace(/[\[\]]/g, '');
    return cleaned.split(',').map(parseFloat);
  }
  
  throw new Error(`Invalid embedding format: ${typeof embedding}`);
}

/**
 * Search for similar chunks with additional ranking by recency.
 * 
 * Combines similarity score with recency for ranking.
 * 
 * @param queryEmbedding - Query embedding vector
 * @param options - Search options
 * @param recencyWeight - Weight for recency (0-1, default: 0.1)
 * @returns Array of search results sorted by combined score
 */
export async function searchSimilarChunksWithRecency(
  queryEmbedding: number[],
  options: VectorSearchOptions,
  recencyWeight: number = 0.1
): Promise<SearchResult[]> {
  const results = await searchSimilarChunks(queryEmbedding, { ...options, topK: options.topK ? options.topK * 2 : 10 });
  
  if (results.length === 0) {
    return [];
  }
  
  // Get email dates for recency calculation
  const supabase = await createServerSupabaseClient();
  const emailIds = [...new Set(results.map(r => r.metadata.emailId))];
  
  const { data: emails } = await supabase
    .from('emails')
    .select('id, received_at')
    .in('id', emailIds);
  
  const emailDates = new Map(
    (emails || []).map(e => [e.id, new Date(e.received_at).getTime()])
  );
  
  const now = Date.now();
  const maxAge = 365 * 24 * 60 * 60 * 1000; // 1 year in milliseconds
  
  // Calculate combined scores
  const scoredResults = results.map(result => {
    const emailDate = emailDates.get(result.metadata.emailId);
    const age = emailDate ? (now - emailDate) / maxAge : 1; // Normalize to 0-1
    const recencyScore = 1 - Math.min(age, 1); // More recent = higher score
    
    const combinedScore = 
      result.similarity * (1 - recencyWeight) + 
      recencyScore * recencyWeight;
    
    return {
      ...result,
      similarity: combinedScore, // Override similarity with combined score
      metadata: {
        ...result.metadata,
        originalSimilarity: result.similarity,
        recencyScore,
      },
    };
  });
  
  // Sort by combined score and return top-k
  scoredResults.sort((a, b) => b.similarity - a.similarity);
  
  return scoredResults.slice(0, options.topK || 5);
}
