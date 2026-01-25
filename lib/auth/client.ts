/**
 * Supabase Auth Client Configuration
 * 
 * Provides client-side and server-side Supabase auth clients.
 */

import { createBrowserClient, createServerClient } from '@supabase/ssr';
import { cookies } from 'next/headers';
import type { Database } from '@/lib/database/types';

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

if (!supabaseUrl || !supabaseAnonKey) {
  throw new Error(
    'Missing Supabase environment variables. Please set NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY in your .env.local file.'
  );
}

/**
 * Create Supabase client for client-side (browser)
 * Uses cookies for session management
 */
export function createClient() {
  return createBrowserClient<Database>(supabaseUrl, supabaseAnonKey);
}

/**
 * Create Supabase client for server-side (Next.js Server Components, API Routes)
 * Uses cookies for session management
 */
export async function createServerSupabaseClient() {
  const cookieStore = await cookies();

  return createServerClient<Database>(supabaseUrl, supabaseAnonKey, {
    cookies: {
      getAll() {
        return cookieStore.getAll();
      },
      setAll(cookiesToSet) {
        try {
          cookiesToSet.forEach(({ name, value, options }) => {
            cookieStore.set(name, value, options);
          });
        } catch {
          // The `setAll` method was called from a Server Component.
          // This can be ignored if you have middleware refreshing
          // user sessions.
        }
      },
    },
  });
}

/**
 * Create Supabase client for middleware
 * Uses cookies for session management
 */
export function createMiddlewareClient(request: Request) {
  return createServerClient<Database>(supabaseUrl, supabaseAnonKey, {
    cookies: {
      getAll() {
        return Object.fromEntries(
          request.headers.get('cookie')?.split('; ').map((cookie) => {
            const [name, ...rest] = cookie.split('=');
            return [name, rest.join('=')];
          }) || []
        );
      },
      setAll(cookiesToSet) {
        // Middleware can't set cookies, so we skip this
        // The middleware will handle session refresh
      },
    },
  });
}
