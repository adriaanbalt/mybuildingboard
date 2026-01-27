/**
 * Configuration Types
 * 
 * Type definitions for application configuration.
 */

export type Environment = 'development' | 'staging' | 'production';

export interface SupabaseConfig {
  url: string;
  anonKey: string;
  serviceRoleKey?: string;
}

export interface OpenAIConfig {
  apiKey: string;
  embeddingModel?: string;
  chatModel?: string;
}

export interface GmailConfig {
  clientId: string;
  clientSecret: string;
  refreshToken?: string;
}

export interface GCPConfig {
  projectId: string;
  serviceAccountKey?: string;
  storageBucket?: string;
}

export interface EmailConfig {
  documentsEmail: string;
  questionsEmail: string;
}

export interface APIConfig {
  baseUrl: string;
  timeout: number;
  rateLimit?: {
    requests: number;
    window: number; // in seconds
  };
}

export interface FeatureFlags {
  [key: string]: boolean;
}

export interface AppConfig {
  environment: Environment;
  supabase: SupabaseConfig;
  openai: OpenAIConfig;
  gmail?: GmailConfig;
  gcp?: GCPConfig;
  email?: EmailConfig;
  api?: APIConfig;
  features?: FeatureFlags;
}
