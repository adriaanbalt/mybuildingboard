/**
 * Gmail API Types
 * 
 * Types specific to Gmail API implementation.
 */

/**
 * Gmail API credentials
 */
export interface GmailCredentials {
  clientId: string;
  clientSecret: string;
  refreshToken: string;
  accessToken?: string; // Auto-refreshed
}

/**
 * Gmail API configuration
 */
export interface GmailConfig {
  providerType: 'gmail';
  credentials: GmailCredentials;
  inboxAddress: string;
}
