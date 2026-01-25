/**
 * Authentication Module
 * 
 * Centralized authentication utilities for the application.
 */

// Client configuration
export * from './client';

// Server-side helpers
export * from './helpers';

// Context and hooks (client-side only)
export { AuthProvider, useAuth, useUser, useSession } from '@/lib/contexts/AuthContext';
