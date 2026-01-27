/**
 * Configuration Loader
 * 
 * Loads configuration from environment variables and validates it.
 */

import { AppConfig, Environment } from './types';
import { validateConfig } from './validation';
import { logger } from '@/lib/errors/logger';

/**
 * Detect current environment
 */
export function detectEnvironment(): Environment {
  const env = process.env.NODE_ENV || 'development';
  
  if (env === 'production') {
    return 'production';
  } else if (env === 'staging' || env === 'test') {
    return 'staging';
  }
  
  return 'development';
}

/**
 * Load configuration from environment variables
 */
export function loadConfigFromEnv(): Partial<AppConfig> {
  const environment = detectEnvironment();

  const config: Partial<AppConfig> = {
    environment,
    supabase: {
      url: process.env.NEXT_PUBLIC_SUPABASE_URL || '',
      anonKey: process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || '',
      serviceRoleKey: process.env.SUPABASE_SERVICE_ROLE_KEY,
    },
    openai: {
      apiKey: process.env.OPENAI_API_KEY || '',
      embeddingModel: process.env.OPENAI_EMBEDDING_MODEL || 'text-embedding-3-small',
      chatModel: process.env.OPENAI_CHAT_MODEL || 'gpt-4',
    },
    gmail: process.env.GMAIL_CLIENT_ID && process.env.GMAIL_CLIENT_SECRET
      ? {
          clientId: process.env.GMAIL_CLIENT_ID,
          clientSecret: process.env.GMAIL_CLIENT_SECRET,
          refreshToken: process.env.GMAIL_REFRESH_TOKEN,
        }
      : undefined,
    gcp: process.env.GCP_PROJECT_ID
      ? {
          projectId: process.env.GCP_PROJECT_ID,
          serviceAccountKey: process.env.GCP_SERVICE_ACCOUNT_KEY,
          storageBucket: process.env.GCP_STORAGE_BUCKET,
        }
      : undefined,
    email: process.env.DOCUMENTS_EMAIL && process.env.QUESTIONS_EMAIL
      ? {
          documentsEmail: process.env.DOCUMENTS_EMAIL,
          questionsEmail: process.env.QUESTIONS_EMAIL,
        }
      : undefined,
    api: {
      baseUrl: process.env.NEXT_PUBLIC_API_URL || process.env.NEXT_PUBLIC_APP_URL || '',
      timeout: parseInt(process.env.API_TIMEOUT || '30000', 10),
      rateLimit: process.env.API_RATE_LIMIT_REQUESTS && process.env.API_RATE_LIMIT_WINDOW
        ? {
            requests: parseInt(process.env.API_RATE_LIMIT_REQUESTS, 10),
            window: parseInt(process.env.API_RATE_LIMIT_WINDOW, 10),
          }
        : undefined,
    },
  };

  return config;
}

/**
 * Load and validate configuration
 * 
 * @throws ValidationError if configuration is invalid
 */
export function loadConfig(): AppConfig {
  try {
    const config = loadConfigFromEnv();
    const validatedConfig = validateConfig(config);
    
    logger.info('Configuration loaded successfully', {
      environment: validatedConfig.environment,
    });
    
    return validatedConfig;
  } catch (error) {
    logger.error('Configuration validation failed', error as Error);
    throw error;
  }
}

/**
 * Get configuration (singleton pattern)
 */
let cachedConfig: AppConfig | null = null;

export function getConfig(): AppConfig {
  if (!cachedConfig) {
    cachedConfig = loadConfig();
  }
  return cachedConfig;
}

/**
 * Reload configuration (useful for testing or config updates)
 */
export function reloadConfig(): AppConfig {
  cachedConfig = null;
  return getConfig();
}
