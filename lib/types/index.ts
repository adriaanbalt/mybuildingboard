/**
 * Shared TypeScript types
 * 
 * This file re-exports types from the shared types specification.
 * See docs/technical-roadmap/specs/shared-types-specification.md for canonical definitions.
 */

// App (Multi-Tenant Container)
export interface App {
  id: string // UUID
  name: string
  subdomain?: string
  createdAt: string // ISO timestamp
  updatedAt: string // ISO timestamp
}

// AppMember (User-Organization Relationship)
export interface AppMember {
  id: string // UUID
  appId: string // UUID
  userId: string // UUID (Supabase Auth user ID)
  role: 'owner' | 'admin' | 'member'
  createdAt: string // ISO timestamp
  updatedAt: string // ISO timestamp
}

// Email
export interface Email {
  id: string // UUID
  appId: string // UUID
  providerId: string // Provider-specific email ID
  providerType: 'gmail' | 'imap' | 'sendgrid' | 'mailgun' | 'microsoft_graph'
  threadId?: string
  senderEmail: string
  senderName?: string
  subject: string
  bodyText?: string
  bodyHtml?: string
  receivedAt: string // ISO timestamp
  status: 'pending' | 'processing' | 'completed' | 'failed'
  createdAt: string // ISO timestamp
  updatedAt: string // ISO timestamp
}

// DocumentChunk
export interface DocumentChunk {
  id: string // UUID
  appId: string // UUID
  emailId: string // UUID
  attachmentId?: string // UUID
  chunkIndex: number
  text: string
  embedding?: number[] // Vector embedding (1536 dimensions for text-embedding-3-small)
  tokenCount: number
  createdAt: string // ISO timestamp
}

// EmailQuery
export interface EmailQuery {
  id: string // UUID
  appId: string // UUID
  threadId?: string // UUID
  queryText: string
  answerText?: string
  sourcesUsed?: string[] // Array of chunk IDs
  status: 'pending' | 'processing' | 'completed' | 'failed'
  createdAt: string // ISO timestamp
  updatedAt: string // ISO timestamp
}
