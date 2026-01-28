/**
 * Server-Side Auth Helpers
 *
 * Provides server-side authentication utilities for API routes and Server Components.
 */

import { AuthenticationError, AuthorizationError } from '@/lib/errors'
import type { Session, User } from '@supabase/supabase-js'
import { redirect } from 'next/navigation'
import type { NextRequest, NextResponse } from 'next/server'
import { createRouteHandlerClient, createServerSupabaseClient } from './server'

/**
 * Require authentication - throws error or redirects if not authenticated
 *
 * @param redirectTo - Optional redirect path if not authenticated (default: '/login')
 * @returns User and session if authenticated
 */
export async function requireAuth(redirectTo: string = '/login'): Promise<{
  user: User
  session: Session
}> {
  const supabase = await createServerSupabaseClient()
  const {
    data: { user },
    error,
  } = await supabase.auth.getUser()

  if (error || !user) {
    redirect(redirectTo)
  }

  // Get session after verifying user
  const {
    data: { session },
  } = await supabase.auth.getSession()

  if (!session) {
    redirect(redirectTo)
  }

  return {
    user,
    session,
  }
}

/**
 * Require authentication for API routes - throws AuthenticationError if not authenticated
 *
 * NOTE: This function uses createServerSupabaseClient which works for Server Components
 * but may not work properly in Route Handlers. For Route Handlers, use requireAuthForRouteHandler instead.
 *
 * @returns User and session if authenticated
 * @throws AuthenticationError if not authenticated
 */
export async function requireAuthForAPI(): Promise<{
  user: User
  session: Session
}> {
  const supabase = await createServerSupabaseClient()
  const {
    data: { user },
    error,
  } = await supabase.auth.getUser()

  if (error || !user) {
    throw new AuthenticationError('Authentication required', {
      error: error?.message,
    })
  }

  // Get session after verifying user
  const {
    data: { session },
  } = await supabase.auth.getSession()

  if (!session) {
    throw new AuthenticationError('Session not found', {
      userId: user.id,
    })
  }

  return {
    user,
    session,
  }
}

/**
 * Require authentication for Route Handlers (API Routes) - throws AuthenticationError if not authenticated
 *
 * This function should be used in Route Handlers (app/api routes) as it properly
 * handles cookies from the request and can set cookies in the response.
 *
 * @param request - NextRequest object from the route handler
 * @param response - NextResponse object from the route handler
 * @returns User and session if authenticated, along with the Supabase client
 * @throws AuthenticationError if not authenticated
 */
export async function requireAuthForRouteHandler(
  request: NextRequest,
  response: NextResponse
): Promise<{
  user: User
  session: Session
  supabase: ReturnType<typeof createRouteHandlerClient>
}> {
  // TLS is automatically configured in createRouteHandlerClient
  const supabase = createRouteHandlerClient(request, response)

  // First validate the user by calling getUser (validates token with Supabase Auth server)
  // This is the secure way to authenticate - getUser() contacts Supabase to verify the token
  const {
    data: { user },
    error: userError,
  } = await supabase.auth.getUser()

  if (userError || !user) {
    // Log detailed error information for debugging
    const cookies = request.cookies.getAll()
    const authCookies = cookies.filter((c) => c.name.includes('auth-token'))
    const cookieHeader = request.headers.get('cookie')

    throw new AuthenticationError('Authentication required', {
      error: userError?.message || 'No valid user found',
      userError: userError?.message,
      userErrorStatus: userError?.status,
      cookieCount: cookies.length,
      authCookieCount: authCookies.length,
      authCookieNames: authCookies.map((c) => c.name),
      hasCookieHeader: !!cookieHeader,
      supabaseUrl: process.env.NEXT_PUBLIC_SUPABASE_URL,
    })
  }

  // Get session after verifying user
  const {
    data: { session },
  } = await supabase.auth.getSession()

  if (!session) {
    throw new AuthenticationError('Session not found', {
      userId: user.id,
    })
  }

  // Explicitly set the session on the client to ensure RLS policies work
  // This ensures auth.uid() returns the correct user ID for RLS evaluation
  const { error: setSessionError } = await supabase.auth.setSession({
    access_token: session.access_token,
    refresh_token: session.refresh_token,
  })

  if (setSessionError) {
    throw new AuthenticationError('Failed to set session', {
      error: setSessionError.message,
      userId: user.id,
    })
  }

  // The session is now set on the client
  // The @supabase/ssr library should automatically include the JWT in database requests
  return {
    user,
    session,
    supabase,
  }
}

/**
 * Get server user - returns user if authenticated, null otherwise
 *
 * @returns User if authenticated, null otherwise
 */
export async function getServerUser(): Promise<User | null> {
  const supabase = await createServerSupabaseClient()
  const {
    data: { user },
    error,
  } = await supabase.auth.getUser()

  if (error || !user) {
    return null
  }

  return user
}

/**
 * Get server session - returns session if authenticated, null otherwise
 *
 * @returns Session if authenticated, null otherwise
 */
export async function getServerSession(): Promise<Session | null> {
  const supabase = await createServerSupabaseClient()

  // First verify user is authenticated
  const {
    data: { user },
    error,
  } = await supabase.auth.getUser()

  if (error || !user) {
    return null
  }

  // Then get session
  const {
    data: { session },
  } = await supabase.auth.getSession()

  return session
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
  const { user } = await requireAuth()

  const supabase = await createServerSupabaseClient()
  const { data, error } = await supabase
    .from('app_members')
    .select('id')
    .eq('app_id', appId as any)
    .eq('user_id', user.id as any)
    .single()

  if (error || !data) {
    redirect(redirectTo)
  }

  return {
    userId: user.id,
    appId,
  }
}

/**
 * Require app membership for API routes - throws error if not member
 *
 * @param appId - App ID to check membership for
 * @returns User ID and App ID if valid
 * @throws AuthorizationError if not a member
 */
export async function requireAppMembershipForAPI(
  appId: string
): Promise<{ userId: string; appId: string }> {
  const { user } = await requireAuthForAPI()

  const supabase = await createServerSupabaseClient()
  const { data, error } = await supabase
    .from('app_members')
    .select('id')
    .eq('app_id', appId as any)
    .eq('user_id', user.id as any)
    .single()

  if (error || !data) {
    throw new AuthorizationError('You are not a member of this app', {
      appId,
      userId: user.id,
    })
  }

  return {
    userId: user.id,
    appId,
  }
}

/**
 * Get user's app memberships
 *
 * @param userId - User ID
 * @returns Array of app memberships
 */
export async function getUserAppMemberships(userId: string) {
  const supabase = await createServerSupabaseClient()
  const { data, error } = await supabase
    .from('app_members')
    .select('app_id, role')
    .eq('user_id', userId as any)

  if (error) {
    throw new AuthenticationError('Failed to get app memberships', { userId })
  }

  return data || []
}

/**
 * Check if user is member of app
 *
 * @param userId - User ID
 * @param appId - App ID
 * @returns True if user is member, false otherwise
 */
export async function isAppMember(userId: string, appId: string): Promise<boolean> {
  const supabase = await createServerSupabaseClient()
  const { data, error } = await supabase
    .from('app_members')
    .select('id')
    .eq('app_id', appId)
    .eq('user_id', userId as any)
    .single()

  return !error && !!data
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
  const supabase = await createServerSupabaseClient()
  const { data, error } = await supabase
    .from('app_members')
    .select('role')
    .eq('app_id', appId)
    .eq('user_id', userId as any)
    .single()

  if (error || !data) {
    return null
  }

  return (data as any).role as 'owner' | 'admin' | 'member'
}

/**
 * Check if user has admin or owner role in app
 *
 * @param userId - User ID
 * @param appId - App ID
 * @returns True if user is admin or owner, false otherwise
 */
export async function isAppAdmin(userId: string, appId: string): Promise<boolean> {
  const role = await getUserAppRole(userId, appId)
  return role === 'admin' || role === 'owner'
}
