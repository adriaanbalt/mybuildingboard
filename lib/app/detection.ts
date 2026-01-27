/**
 * App ID Detection
 *
 * Detects app_id from various sources (user membership, headers, cookies, subdomain).
 */

import { getServerUser } from '@/lib/auth/helpers'
import { createServerSupabaseClient } from '@/lib/auth/server'

/**
 * Get app ID from user's app memberships
 *
 * Priority:
 * 1. If user is member of exactly one app → return that app_id
 * 2. If user is member of multiple apps → return first app_id (or use cookie/header)
 * 3. If user is member of no apps → return null
 */
export async function getAppIdFromUserMembership(): Promise<string | null> {
  const user = await getServerUser()
  if (!user) {
    return null
  }

  const supabase = await createServerSupabaseClient()
  const { data, error } = await supabase
    .from('app_members')
    .select('app_id')
    .eq('user_id', user.id)
    .limit(1)
    .single()

  if (error || !data) {
    return null
  }

  return data.app_id
}

/**
 * Get all app IDs user is a member of
 */
export async function getUserAppIds(): Promise<string[]> {
  const user = await getServerUser()
  if (!user) {
    return []
  }

  const supabase = await createServerSupabaseClient()
  const { data, error } = await supabase.from('app_members').select('app_id').eq('user_id', user.id)

  if (error || !data) {
    return []
  }

  return data.map((member) => member.app_id)
}

/**
 * Get app ID from request headers
 */
export function getAppIdFromHeaders(headers: Headers): string | null {
  return headers.get('x-app-id') || null
}

/**
 * Get app ID from cookies
 */
export function getAppIdFromCookies(cookies: {
  get: (name: string) => { value: string } | undefined
}): string | null {
  const appIdCookie = cookies.get('app_id')
  return appIdCookie?.value || null
}

/**
 * Get app ID from subdomain (future enhancement)
 *
 * Example: building1.mybuildingboard.com → returns app_id for subdomain "building1"
 */
export async function getAppIdFromSubdomain(hostname: string): Promise<string | null> {
  // Extract subdomain from hostname
  const parts = hostname.split('.')
  if (parts.length < 3) {
    return null // No subdomain
  }

  const subdomain = parts[0]
  if (!subdomain || subdomain === 'www' || subdomain === 'localhost') {
    return null
  }

  // Look up app by subdomain
  const supabase = await createServerSupabaseClient()
  const { data, error } = await supabase
    .from('apps')
    .select('id')
    .eq('subdomain', subdomain)
    .single()

  if (error || !data) {
    return null
  }

  return data.id
}

/**
 * Validate app ID exists in database
 */
export async function validateAppId(appId: string): Promise<boolean> {
  const supabase = await createServerSupabaseClient()
  const { data, error } = await supabase.from('apps').select('id').eq('id', appId).single()

  return !error && !!data
}

/**
 * Get app ID from request (priority order)
 *
 * Priority:
 * 1. Header (x-app-id) - highest priority (explicit selection)
 * 2. Cookie (app_id) - user's selected app
 * 3. User membership (single app) - automatic if user has one app
 * 4. Subdomain (future) - for white-labeling
 *
 * Note: This function requires async operations and should be used in server contexts.
 * For middleware, use the individual functions directly.
 */
export async function getAppIdFromRequest(
  headers: Headers,
  cookies: { get: (name: string) => { value: string } | undefined },
  hostname?: string
): Promise<string | null> {
  // 1. Check header (explicit selection)
  const headerAppId = getAppIdFromHeaders(headers)
  if (headerAppId && (await validateAppId(headerAppId))) {
    return headerAppId
  }

  // 2. Check cookie (user's selected app)
  const cookieAppId = getAppIdFromCookies(cookies)
  if (cookieAppId && (await validateAppId(cookieAppId))) {
    return cookieAppId
  }

  // 3. Check user membership (automatic if single app)
  const membershipAppId = await getAppIdFromUserMembership()
  if (membershipAppId) {
    return membershipAppId
  }

  // 4. Check subdomain (future enhancement)
  if (hostname) {
    const subdomainAppId = await getAppIdFromSubdomain(hostname)
    if (subdomainAppId) {
      return subdomainAppId
    }
  }

  return null
}
