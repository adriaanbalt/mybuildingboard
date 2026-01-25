/**
 * Server-Side Auth Helpers
 * 
 * Provides server-side authentication utilities for API routes and Server Components.
 */

import { createServerSupabaseClient } from './client';
import { AuthenticationError, AuthorizationError } from '@/lib/errors';
import { redirect } from 'next/navigation';
import type { User, Session } from '@supabase/supabase-js';

/**
 * Require authentication - throws error or redirects if not authenticated
 * 
 * @param redirectTo - Optional redirect path if not authenticated (default: '/login')
 * @returns User and session if authenticated
 */
export async function requireAuth(redirectTo: string = '/login'): Promise<{
  user: User;
  session: Session;
}> {
  const supabase = await createServerSupabaseClient();
  const {
    data: { session },
    error,
  } = await supabase.auth.getSession();

  if (error || !session || !session.user) {
    redirect(redirectTo);
  }

  return {
    user: session.user,
    session,
  };
}

/**
 * Get server user - returns user if authenticated, null otherwise
 * 
 * @returns User if authenticated, null otherwise
 */
export async function getServerUser(): Promise<User | null> {
  const supabase = await createServerSupabaseClient();
  const {
    data: { session },
  } = await supabase.auth.getSession();

  return session?.user ?? null;
}

/**
 * Get server session - returns session if authenticated, null otherwise
 * 
 * @returns Session if authenticated, null otherwise
 */
export async function getServerSession(): Promise<Session | null> {
  const supabase = await createServerSupabaseClient();
  const {
    data: { session },
  } = await supabase.auth.getSession();

  return session;
}

/**
 * Require app membership - checks if user is member of app
 * 
 * @param appId - App ID to check membership for
 * @param redirectTo - Optional redirect path if not member (default: '/dashboard')
 * @returns User ID and App ID if valid
 */
export async function requireAppMembership(
  appId: string,
  redirectTo: string = '/dashboard'
): Promise<{ userId: string; appId: string }> {
  const { user } = await requireAuth();

  const supabase = await createServerSupabaseClient();
  const { data, error } = await supabase
    .from('app_members')
    .select('id')
    .eq('app_id', appId)
    .eq('user_id', user.id)
    .single();

  if (error || !data) {
    redirect(redirectTo);
  }

  return {
    userId: user.id,
    appId,
  };
}

/**
 * Get user's app memberships
 * 
 * @param userId - User ID
 * @returns Array of app memberships
 */
export async function getUserAppMemberships(userId: string) {
  const supabase = await createServerSupabaseClient();
  const { data, error } = await supabase
    .from('app_members')
    .select('app_id, role')
    .eq('user_id', userId);

  if (error) {
    throw new AuthenticationError('Failed to get app memberships', { userId });
  }

  return data || [];
}

/**
 * Check if user is member of app
 * 
 * @param userId - User ID
 * @param appId - App ID
 * @returns True if user is member, false otherwise
 */
export async function isAppMember(userId: string, appId: string): Promise<boolean> {
  const supabase = await createServerSupabaseClient();
  const { data, error } = await supabase
    .from('app_members')
    .select('id')
    .eq('app_id', appId)
    .eq('user_id', userId)
    .single();

  return !error && !!data;
}

/**
 * Get user's role in app
 * 
 * @param userId - User ID
 * @param appId - App ID
 * @returns User's role ('owner', 'admin', 'member') or null if not a member
 */
export async function getUserAppRole(
  userId: string,
  appId: string
): Promise<'owner' | 'admin' | 'member' | null> {
  const supabase = await createServerSupabaseClient();
  const { data, error } = await supabase
    .from('app_members')
    .select('role')
    .eq('app_id', appId)
    .eq('user_id', userId)
    .single();

  if (error || !data) {
    return null;
  }

  return data.role as 'owner' | 'admin' | 'member';
}

/**
 * Check if user has admin or owner role in app
 * 
 * @param userId - User ID
 * @param appId - App ID
 * @returns True if user is admin or owner, false otherwise
 */
export async function isAppAdmin(userId: string, appId: string): Promise<boolean> {
  const role = await getUserAppRole(userId, appId);
  return role === 'admin' || role === 'owner';
}
