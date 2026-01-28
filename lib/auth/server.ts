/**
 * Supabase Auth Client Configuration (Server-Side Only)
 *
 * Provides server-side Supabase auth clients for use in Server Components, API Routes, and Middleware.
 */

import type { Database } from '@/lib/database/types'
import { configureLocalTLS } from '@/lib/utils/tls'
import { createServerClient } from '@supabase/ssr'
import { cookies } from 'next/headers'
import type { NextRequest, NextResponse } from 'next/server'

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY

if (!supabaseUrl || !supabaseAnonKey) {
  throw new Error(
    'Missing Supabase environment variables. Please set NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY in your .env.local file.'
  )
}

/**
 * Create Supabase client for server-side (Next.js Server Components, API Routes)
 * Uses cookies for session management
 * 
 * Automatically configures TLS for localhost in development to accept self-signed certificates
 */
export async function createServerSupabaseClient() {
  // Configure TLS for localhost (disable SSL verification for self-signed certs)
  configureLocalTLS(supabaseUrl)
  
  const cookieStore = await cookies()

  return createServerClient<Database>(supabaseUrl, supabaseAnonKey, {
    cookies: {
      getAll() {
        return cookieStore.getAll()
      },
      setAll(cookiesToSet) {
        try {
          cookiesToSet.forEach(({ name, value, options }) => {
            cookieStore.set(name, value, options)
          })
        } catch {
          // The `setAll` method was called from a Server Component.
          // This can be ignored if you have middleware refreshing
          // user sessions.
        }
      },
    },
  })
}

/**
 * Create Supabase client for middleware
 * Uses cookies for session management
 * 
 * Automatically configures TLS for localhost in development to accept self-signed certificates
 */
export function createMiddlewareClient(request: Request) {
  // Configure TLS for localhost (disable SSL verification for self-signed certs)
  configureLocalTLS(supabaseUrl)
  
  return createServerClient<Database>(supabaseUrl, supabaseAnonKey, {
    cookies: {
      getAll() {
        return request.headers
          .get('cookie')
          ?.split('; ')
          .map((cookie) => {
            const [name, ...rest] = cookie.split('=')
            return { name, value: decodeURIComponent(rest.join('=')) }
          }) || []
      },
      setAll(cookiesToSet) {
        // Middleware can't set cookies, so we skip this
        // The middleware will handle session refresh
      },
    },
  })
}

/**
 * Create Supabase client for Route Handlers (API Routes)
 * Uses cookies from request and can set cookies in response
 * 
 * Automatically configures TLS for localhost in development to accept self-signed certificates
 */
export function createRouteHandlerClient(
  request: NextRequest,
  response: NextResponse
) {
  // Configure TLS for localhost (disable SSL verification for self-signed certs)
  configureLocalTLS(supabaseUrl)
  
  return createServerClient<Database>(supabaseUrl, supabaseAnonKey, {
    cookies: {
      getAll() {
        // Try using request.cookies first (Next.js 15 way)
        const cookies = request.cookies.getAll()
        if (cookies.length > 0) {
          return cookies.map((cookie) => ({
            name: cookie.name,
            value: cookie.value,
          }))
        }
        
        // Fallback to parsing cookie header manually (like middleware)
        // This handles cases where cookies might not be parsed correctly
        const cookieHeader = request.headers.get('cookie')
        if (cookieHeader) {
          return cookieHeader
            .split('; ')
            .map((cookie) => {
              const [name, ...rest] = cookie.split('=')
              return { 
                name: name.trim(), 
                value: decodeURIComponent(rest.join('=')) 
              }
            })
        }
        
        return []
      },
      setAll(cookiesToSet) {
        cookiesToSet.forEach(({ name, value, options }) => {
          response.cookies.set(name, value, options)
        })
      },
    },
  })
}
