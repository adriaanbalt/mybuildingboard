/**
 * Server-Side App Helpers
 * 
 * Provides server-side utilities for app context and membership verification.
 */

import { cookies, headers } from 'next/headers';
import { getAppIdFromRequest, validateAppId } from './detection';
import { getAppConfig, getApp } from './config';
import { requireAuth } from '@/lib/auth/helpers';
import { requireAppMembership as authRequireAppMembership } from '@/lib/auth/helpers';
import { NotFoundError, AuthorizationError } from '@/lib/errors';
import type { AppWithConfig } from './types';

/**
 * Get current app ID from request
 * 
 * Extracts app_id from headers, cookies, or user membership.
 * Works in Server Components and API routes.
 */
export async function getCurrentAppId(): Promise<string | null> {
  const headersList = await headers();
  const cookieStore = await cookies();
  const hostname = headersList.get('host') || undefined;

  return getAppIdFromRequest(headersList, cookieStore, hostname);
}

/**
 * Get current app configuration
 * 
 * Loads app config from database/cache.
 * Returns null if app not found or user not authenticated.
 */
export async function getCurrentAppConfig(): Promise<AppWithConfig | null> {
  const appId = await getCurrentAppId();
  if (!appId) {
    return null;
  }

  return getAppConfig(appId);
}

/**
 * Require app membership (server-side)
 * 
 * Verifies user is authenticated and is a member of the app.
 * Throws error if not authenticated or not a member.
 * 
 * @param appId - Optional app ID (uses current app if not provided)
 * @returns App ID and user ID if valid
 */
export async function requireAppMembership(appId?: string): Promise<{
  appId: string;
  userId: string;
}> {
  const { user } = await requireAuth();

  const currentAppId = appId || (await getCurrentAppId());
  if (!currentAppId) {
    throw new NotFoundError('App not found');
  }

  // Validate app exists
  const isValid = await validateAppId(currentAppId);
  if (!isValid) {
    throw new NotFoundError('App not found');
  }

  // Verify membership
  const result = await authRequireAppMembership(currentAppId);
  return result;
}

/**
 * Get app with membership check
 * 
 * Returns app if user is a member, throws error otherwise.
 */
export async function getAppWithMembership(appId?: string): Promise<AppWithConfig> {
  const { appId: verifiedAppId } = await requireAppMembership(appId);

  const app = await getAppConfig(verifiedAppId);
  if (!app) {
    throw new NotFoundError('App not found');
  }

  return app;
}

/**
 * Check if user is member of app
 */
export async function isAppMember(appId: string): Promise<boolean> {
  try {
    await requireAppMembership(appId);
    return true;
  } catch {
    return false;
  }
}
