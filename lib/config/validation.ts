/**
 * Configuration Validation
 * 
 * Validates configuration values and formats.
 */

import { AppConfig, Environment } from './types';
import { ValidationError } from '@/lib/errors';

/**
 * Validate URL format
 */
export function validateUrl(url: string, fieldName: string): void {
  try {
    new URL(url);
  } catch {
    throw new ValidationError(`Invalid ${fieldName}: must be a valid URL`, {
      field: fieldName,
      value: url,
    });
  }
}

/**
 * Validate email format
 */
export function validateEmail(email: string, fieldName: string): void {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!emailRegex.test(email)) {
    throw new ValidationError(`Invalid ${fieldName}: must be a valid email address`, {
      field: fieldName,
      value: email,
    });
  }
}

/**
 * Validate required field
 */
export function validateRequired<T>(value: T | undefined | null, fieldName: string): T {
  if (value === undefined || value === null || value === '') {
    throw new ValidationError(`Missing required field: ${fieldName}`, {
      field: fieldName,
    });
  }
  return value;
}

/**
 * Validate number range
 */
export function validateRange(
  value: number,
  fieldName: string,
  min?: number,
  max?: number
): void {
  if (min !== undefined && value < min) {
    throw new ValidationError(`Invalid ${fieldName}: must be >= ${min}`, {
      field: fieldName,
      value,
      min,
    });
  }
  if (max !== undefined && value > max) {
    throw new ValidationError(`Invalid ${fieldName}: must be <= ${max}`, {
      field: fieldName,
      value,
      max,
    });
  }
}

/**
 * Validate environment
 */
export function validateEnvironment(env: string): Environment {
  if (env !== 'development' && env !== 'staging' && env !== 'production') {
    throw new ValidationError(`Invalid NODE_ENV: must be development, staging, or production`, {
      field: 'NODE_ENV',
      value: env,
    });
  }
  return env as Environment;
}

/**
 * Validate configuration
 */
export function validateConfig(config: Partial<AppConfig>): AppConfig {
  // Validate environment
  const environment = validateEnvironment(
    config.environment || process.env.NODE_ENV || 'development'
  );

  // Validate Supabase config
  const supabaseUrl = validateRequired(config.supabase?.url, 'supabase.url');
  validateUrl(supabaseUrl, 'supabase.url');

  const supabaseAnonKey = validateRequired(config.supabase?.anonKey, 'supabase.anonKey');
  if (!supabaseAnonKey || supabaseAnonKey.length < 20) {
    throw new ValidationError('Invalid supabase.anonKey: key too short', {
      field: 'supabase.anonKey',
    });
  }

  // Validate OpenAI config
  const openaiApiKey = validateRequired(config.openai?.apiKey, 'openai.apiKey');
  if (!openaiApiKey.startsWith('sk-')) {
    throw new ValidationError('Invalid openai.apiKey: must start with "sk-"', {
      field: 'openai.apiKey',
    });
  }

  // Validate API config if provided
  if (config.api) {
    if (config.api.timeout !== undefined) {
      validateRange(config.api.timeout, 'api.timeout', 1000, 60000); // 1s to 60s
    }
  }

  // Validate email config if provided
  if (config.email) {
    validateEmail(config.email.documentsEmail, 'email.documentsEmail');
    validateEmail(config.email.questionsEmail, 'email.questionsEmail');
  }

  return {
    environment,
    supabase: {
      url: supabaseUrl,
      anonKey: supabaseAnonKey,
      serviceRoleKey: config.supabase?.serviceRoleKey,
    },
    openai: {
      apiKey: openaiApiKey,
      embeddingModel: config.openai?.embeddingModel || 'text-embedding-3-small',
      chatModel: config.openai?.chatModel || 'gpt-4',
    },
    gmail: config.gmail,
    gcp: config.gcp,
    email: config.email,
    api: config.api,
    features: config.features,
  };
}
