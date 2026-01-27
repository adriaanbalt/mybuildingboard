/**
 * Authentication Module (Client-Side)
 *
 * Centralized authentication utilities for client components.
 *
 * For server-side helpers, import directly from:
 * - @/lib/auth/server - Server Supabase clients
 * - @/lib/auth/helpers - Server-side auth utilities
 */

// Client configuration
export * from './client'

// Context and hooks (client-side only)
export { AuthProvider, useAuth, useSession, useUser } from '@/lib/contexts/AuthContext'
