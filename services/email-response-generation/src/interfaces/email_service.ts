/**
 * EmailService Interface
 * 
 * Provider-agnostic interface for email services.
 * Enables swapping providers (Gmail API, IMAP, SendGrid, etc.) without refactoring.
 */

import type {
  Email,
  EmailAttachment,
  Inbox,
  ProviderCapabilities,
  WatchHandle,
} from '../types/email';

/**
 * EmailService interface
 * 
 * All email providers must implement this interface.
 */
export interface EmailService {
  /**
   * Fetch emails from inbox
   * 
   * @param inbox - Inbox address or identifier
   * @param since - Optional date to fetch emails since
   * @returns Array of emails
   */
  fetchEmails(inbox: string, since?: Date): Promise<Email[]>;

  /**
   * Get email by provider-specific ID
   * 
   * @param emailId - Provider-specific email ID
   * @returns Email or null if not found
   */
  getEmailById(emailId: string): Promise<Email | null>;

  /**
   * Mark email as processed (label, read, etc.)
   * 
   * @param emailId - Provider-specific email ID
   * @param label - Optional label/folder name
   */
  markAsProcessed(emailId: string, label?: string): Promise<void>;

  /**
   * Send email
   * 
   * @param to - Recipient email address
   * @param subject - Email subject
   * @param body - Plain text body
   * @param htmlBody - Optional HTML body
   * @param inReplyTo - Optional email ID to reply to
   */
  sendEmail(
    to: string,
    subject: string,
    body: string,
    htmlBody?: string,
    inReplyTo?: string
  ): Promise<void>;

  /**
   * Get email attachment
   * 
   * @param emailId - Provider-specific email ID
   * @param attachmentId - Provider-specific attachment ID
   * @returns Attachment data as Buffer
   */
  getAttachment(emailId: string, attachmentId: string): Promise<Buffer>;

  /**
   * List available inboxes
   * 
   * @returns Array of inboxes
   */
  listInboxes(): Promise<Inbox[]>;

  /**
   * Watch inbox for new emails (webhooks, push notifications)
   * 
   * @param inbox - Inbox address or identifier
   * @param callback - Callback function for new emails
   * @returns Watch handle to stop watching
   */
  watchInbox(inbox: string, callback: (email: Email) => void): Promise<WatchHandle>;

  /**
   * Get provider name
   * 
   * @returns Provider name (e.g., "gmail", "imap", "sendgrid")
   */
  getProviderName(): string;

  /**
   * Get provider capabilities
   * 
   * @returns Provider capabilities
   */
  getProviderCapabilities(): ProviderCapabilities;
}
