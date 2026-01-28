/**
 * Supabase Database Client
 *
 * Creates and exports the Supabase client for database operations.
 */

import { logger } from '@/lib/errors/logger'
import { createClient as createSupabaseClient } from '@supabase/supabase-js'
import type { Database } from './types'

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY

if (!supabaseUrl || !supabaseAnonKey) {
  throw new Error(
    'Missing Supabase environment variables. Please set NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY in your .env.local file.'
  )
}

/**
 * Supabase client for client-side operations (browser)
 * Uses anon key - RLS policies enforce security
 */
export const supabase = createSupabaseClient<Database>(supabaseUrl!, supabaseAnonKey!, {
  auth: {
    persistSession: true,
    autoRefreshToken: true,
  },
})

/**
 * Create a Supabase client for server-side operations
 * Can use service role key for admin operations (use with caution)
 */
export function createServerClient() {
  const serviceRoleKey = process.env.SUPABASE_SERVICE_ROLE_KEY

  if (!serviceRoleKey) {
    // Fall back to anon key if service role key not available
    return createSupabaseClient<Database>(supabaseUrl!, supabaseAnonKey!)
  }

  return createSupabaseClient<Database>(supabaseUrl!, serviceRoleKey, {
    auth: {
      autoRefreshToken: false,
      persistSession: false,
    },
  })
}

/**
 * Get Supabase admin client for server-side operations
 * Uses service role key for admin operations (bypasses RLS)
 * Singleton pattern to reuse the same client instance
 */
let adminClient: ReturnType<typeof createSupabaseClient<Database>> | null = null

export function getSupabaseAdmin() {
  if (!adminClient) {
    const serviceRoleKey = process.env.SUPABASE_SERVICE_ROLE_KEY

    if (!serviceRoleKey) {
      throw new Error('Missing SUPABASE_SERVICE_ROLE_KEY. Required for admin operations.')
    }

    // Log admin client creation (without exposing the full key)
    const keyPrefix = serviceRoleKey.substring(0, 20)
    const keySuffix = serviceRoleKey.substring(serviceRoleKey.length - 10)
    logger.debug('Creating admin client with service role key', {
      keyPrefix: `${keyPrefix}...`,
      keySuffix: `...${keySuffix}`,
      keyLength: serviceRoleKey.length,
      supabaseUrl,
    })

    // Create admin client with service role key
    // This bypasses RLS and doesn't use JWT authentication
    // CRITICAL: The Supabase client automatically adds an Authorization header
    // when it detects a session (even from cookies). We must use a custom fetch
    // to explicitly remove the Authorization header and ensure only the apikey
    // header with the service role key is sent to PostgREST.
    adminClient = createSupabaseClient<Database>(supabaseUrl!, serviceRoleKey, {
      auth: {
        autoRefreshToken: false,
        persistSession: false,
        detectSessionInUrl: false, // Prevent detecting sessions from URL params
        // Explicitly disable JWT token usage - use only the service role key
        storage: undefined,
      },
      global: {
        // Use custom fetch to ensure only apikey header is set (no Authorization header)
        // This prevents PostgREST from trying to decode a user JWT
        // PostgREST will use the service role key from apikey header to bypass RLS
        fetch: (url, options = {}) => {
          // Create new headers object to avoid mutating the original
          const headers = new Headers(options.headers)

          // CRITICAL: PostgREST requires BOTH headers for service role authentication:
          // 1. apikey header with the service role key
          // 2. Authorization header with "Bearer <service_role_key>"
          //
          // The Supabase client may add an Authorization header with a user JWT if it detects
          // a session from cookies. We must replace it with the service role key.
          const existingAuthHeader = headers.get('Authorization') || headers.get('authorization')
          if (existingAuthHeader && !existingAuthHeader.includes(serviceRoleKey.substring(0, 20))) {
            // This is a user JWT, not the service role key - replace it
            logger.debug('Replacing user JWT with service role key in Authorization header', {
              hadUserJWT: true,
              userJWTPrefix: existingAuthHeader.substring(0, 30),
            })
          }

          // Set both headers required by PostgREST for service role authentication
          headers.set('apikey', serviceRoleKey)
          headers.set('Authorization', `Bearer ${serviceRoleKey}`)

          // Set standard headers
          headers.set('Content-Type', 'application/json')
          headers.set('Accept', 'application/json')

          logger.debug('Admin client fetch request', {
            url: url.toString(),
            method: options.method || 'GET',
            hasApikey: headers.has('apikey'),
            hasAuthorization: headers.has('Authorization') || headers.has('authorization'),
            headerNames: Array.from(headers.keys()),
            apikeyPrefix: headers.get('apikey')?.substring(0, 20),
            authHeaderPrefix: headers.get('Authorization')?.substring(0, 30),
          })

          // Create a new options object to avoid mutating the original
          const fetchOptions: RequestInit = {
            ...options,
            headers,
            // Ensure we don't pass any credentials that might include cookies
            credentials: 'omit',
          }

          return fetch(url, fetchOptions)
        },
      },
    })

    // Note: We don't need to explicitly clear sessions because:
    // 1. The custom fetch removes any Authorization header
    // 2. persistSession: false prevents session persistence
    // 3. storage: undefined prevents session storage
    // 4. credentials: 'omit' in fetch prevents cookies from being sent

    logger.debug('Admin client created successfully', {
      supabaseUrl,
    })
  }

  return adminClient
}

// Re-export for convenience
export { createClient } from '@supabase/supabase-js'
