/**
 * Vector Search Types
 * 
 * Type definitions for vector search operations.
 */

export interface VectorSearchOptions {
  appId: string;
  topK?: number; // Default: 5
  similarityThreshold?: number; // Default: 0.0 (no threshold)
  emailId?: string;
  attachmentId?: string;
  dateFrom?: Date;
  dateTo?: Date;
  contentType?: string;
}

export interface SearchResult {
  chunkId: string;
  content: string;
  similarity: number; // Cosine similarity score (0-1)
  metadata: {
    emailId: string;
    attachmentId?: string;
    chunkIndex: number;
    appId: string;
    [key: string]: any;
  };
  source: {
    emailId: string;
    emailSubject?: string;
    attachmentId?: string;
    attachmentFilename?: string;
  };
}
