/**
 * Email Service Types
 * 
 * Provider-agnostic types for email operations.
 */

/**
 * Email attachment
 */
export interface EmailAttachment {
  id: string; // Provider-specific attachment ID
  filename: string;
  contentType: string;
  size: number;
  data?: Buffer; // Optional: inline data
}

/**
 * Email sender information
 */
export interface EmailSender {
  email: string;
  name?: string;
}

/**
 * Email recipients
 */
export interface EmailRecipients {
  to: string[];
  cc?: string[];
  bcc?: string[];
}

/**
 * Provider-agnostic Email model
 */
export interface Email {
  id: string; // Provider-specific ID (Gmail ID, IMAP UID, etc.)
  providerType: string; // "gmail", "imap", "sendgrid", etc.
  threadId?: string; // Thread/conversation ID (if supported)
  sender: EmailSender;
  recipients: EmailRecipients;
  subject: string;
  bodyText: string;
  bodyHtml?: string;
  receivedAt: Date;
  attachments?: EmailAttachment[];
  metadata?: Record<string, any>; // Provider-specific metadata
}

/**
 * Inbox information
 */
export interface Inbox {
  id: string;
  name: string;
  address: string;
}

/**
 * Rate limit information
 */
export interface RateLimitInfo {
  requestsPerSecond?: number;
  requestsPerMinute?: number;
  requestsPerHour?: number;
  requestsPerDay?: number;
  quotaUnits?: number; // For Gmail API quota units
}

/**
 * Provider capabilities
 */
export interface ProviderCapabilities {
  supportsWebhooks: boolean; // Can receive push notifications
  supportsPolling: boolean; // Can poll for emails
  supportsLabels: boolean; // Can use labels/folders
  supportsThreading: boolean; // Supports email threading
  maxAttachmentSize: number; // Max attachment size in bytes
  rateLimits: RateLimitInfo; // Rate limit information
  authenticationType: string; // "oauth2", "api_key", "password", etc.
}

/**
 * Watch handle for inbox watching
 */
export interface WatchHandle {
  id: string;
  stop: () => Promise<void>;
}
