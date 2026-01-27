/**
 * Supabase Database Client
 * 
 * Creates and exports the Supabase client for database operations.
 */

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
export const supabase = createSupabaseClient<Database>(supabaseUrl, supabaseAnonKey, {
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
    return createSupabaseClient<Database>(supabaseUrl, supabaseAnonKey)
  }

  return createSupabaseClient<Database>(supabaseUrl, serviceRoleKey, {
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
      throw new Error(
        'Missing SUPABASE_SERVICE_ROLE_KEY. Required for admin operations.'
      )
    }

    adminClient = createSupabaseClient<Database>(supabaseUrl, serviceRoleKey, {
      auth: {
        autoRefreshToken: false,
        persistSession: false,
      },
    })
  }

  return adminClient
}

// Re-export for convenience
export { createClient } from '@supabase/supabase-js'
