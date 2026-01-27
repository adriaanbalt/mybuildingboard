/**
 * Secret Management
 * 
 * Integrates with GCP Secret Manager for secure secret storage.
 * Falls back to environment variables in development.
 */

import { logger } from '@/lib/errors/logger';

/**
 * Secret cache (in-memory)
 */
const secretCache = new Map<string, { value: string; timestamp: number }>();
const CACHE_TTL = 5 * 60 * 1000; // 5 minutes

/**
 * Load secret from GCP Secret Manager
 * 
 * @param secretName - Name of the secret in Secret Manager
 * @returns Secret value or null if not found
 */
export async function loadSecretFromGCP(secretName: string): Promise<string | null> {
  // Only use GCP Secret Manager in production/staging
  const env = process.env.NODE_ENV;
  if (env === 'development' || !process.env.GCP_PROJECT_ID) {
    logger.debug('Skipping GCP Secret Manager in development', { secretName });
    return null;
  }

  try {
    // Check cache first
    const cached = secretCache.get(secretName);
    if (cached && Date.now() - cached.timestamp < CACHE_TTL) {
      return cached.value;
    }

    // TODO: Implement GCP Secret Manager client
    // For now, return null and use environment variables
    // When implementing:
    // const { SecretManagerServiceClient } = require('@google-cloud/secret-manager');
    // const client = new SecretManagerServiceClient();
    // const [version] = await client.accessSecretVersion({
    //   name: `projects/${process.env.GCP_PROJECT_ID}/secrets/${secretName}/versions/latest`,
    // });
    // const secretValue = version.payload?.data?.toString();
    
    logger.debug('GCP Secret Manager not yet implemented, using environment variables', {
      secretName,
    });
    
    return null;
  } catch (error) {
    logger.error('Failed to load secret from GCP Secret Manager', error as Error, {
      secretName,
    });
    return null;
  }
}

/**
 * Get secret value (from Secret Manager or environment variable)
 * 
 * Priority:
 * 1. GCP Secret Manager (production/staging)
 * 2. Environment variable (development/fallback)
 * 
 * @param secretName - Name of the secret
 * @param envVarName - Environment variable name (fallback)
 * @returns Secret value or null
 */
export async function getSecret(secretName: string, envVarName?: string): Promise<string | null> {
  // Try GCP Secret Manager first
  const secretValue = await loadSecretFromGCP(secretName);
  if (secretValue) {
    return secretValue;
  }

  // Fall back to environment variable
  if (envVarName) {
    const envValue = process.env[envVarName];
    if (envValue) {
      return envValue;
    }
  }

  return null;
}

/**
 * Invalidate secret cache
 */
export function invalidateSecretCache(secretName?: string): void {
  if (secretName) {
    secretCache.delete(secretName);
  } else {
    secretCache.clear();
  }
}
