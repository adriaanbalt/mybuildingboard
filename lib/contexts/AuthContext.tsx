'use client';

/**
 * AuthContext Provider
 * 
 * Provides authentication state and methods throughout the application.
 */

import React, { createContext, useContext, useEffect, useState, useCallback } from 'react';
import { createClient } from '@/lib/auth/client';
import type { User, Session } from '@supabase/supabase-js';
import { logger } from '@/lib/errors/logger';

interface AuthContextType {
  user: User | null;
  session: Session | null;
  loading: boolean;
  signIn: (email: string, password: string) => Promise<{ error: Error | null }>;
  signUp: (email: string, password: string) => Promise<{ error: Error | null }>;
  signOut: () => Promise<void>;
  signInWithOAuth: (provider: 'google' | 'github') => Promise<void>;
  refreshSession: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [session, setSession] = useState<Session | null>(null);
  const [loading, setLoading] = useState(true);
  const supabase = createClient();

  /**
   * Initialize auth state
   */
  useEffect(() => {
    // Get initial session
    supabase.auth.getSession().then(({ data: { session } }) => {
      setSession(session);
      setUser(session?.user ?? null);
      setLoading(false);
    });

    // Listen for auth changes
    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, session) => {
      setSession(session);
      setUser(session?.user ?? null);
      setLoading(false);

      // Log auth state changes
      if (session) {
        logger.info('User authenticated', {
          userId: session.user.id,
          email: session.user.email,
        });
      } else {
        logger.info('User signed out');
      }
    });

    return () => {
      subscription.unsubscribe();
    };
  }, [supabase.auth]);

  /**
   * Auto-refresh session before expiry
   */
  useEffect(() => {
    if (!session) return;

    const refreshInterval = setInterval(async () => {
      const { data: { session: currentSession } } = await supabase.auth.getSession();
      
      if (currentSession) {
        // Check if session expires in less than 5 minutes
        const expiresAt = currentSession.expires_at;
        if (expiresAt) {
          const expiresIn = expiresAt * 1000 - Date.now();
          if (expiresIn < 5 * 60 * 1000) {
            // Refresh session
            await supabase.auth.refreshSession();
            logger.debug('Session refreshed automatically');
          }
        }
      }
    }, 60 * 1000); // Check every minute

    return () => clearInterval(refreshInterval);
  }, [session, supabase.auth]);

  /**
   * Sign in with email and password
   */
  const signIn = useCallback(
    async (email: string, password: string) => {
      try {
        const { data, error } = await supabase.auth.signInWithPassword({
          email,
          password,
        });

        if (error) {
          logger.error('Sign in failed', error, { email });
          return { error };
        }

        logger.info('User signed in', { userId: data.user?.id, email });
        return { error: null };
      } catch (error) {
        logger.error('Sign in error', error as Error, { email });
        return { error: error as Error };
      }
    },
    [supabase.auth]
  );

  /**
   * Sign up with email and password
   */
  const signUp = useCallback(
    async (email: string, password: string) => {
      try {
        const { data, error } = await supabase.auth.signUp({
          email,
          password,
        });

        if (error) {
          logger.error('Sign up failed', error, { email });
          return { error };
        }

        logger.info('User signed up', { userId: data.user?.id, email });
        return { error: null };
      } catch (error) {
        logger.error('Sign up error', error as Error, { email });
        return { error: error as Error };
      }
    },
    [supabase.auth]
  );

  /**
   * Sign out
   */
  const signOut = useCallback(async () => {
    try {
      const { error } = await supabase.auth.signOut();
      if (error) {
        logger.error('Sign out failed', error);
        throw error;
      }
      logger.info('User signed out');
    } catch (error) {
      logger.error('Sign out error', error as Error);
      throw error;
    }
  }, [supabase.auth]);

  /**
   * Sign in with OAuth provider
   */
  const signInWithOAuth = useCallback(
    async (provider: 'google' | 'github') => {
      try {
        const { error } = await supabase.auth.signInWithOAuth({
          provider,
          options: {
            redirectTo: `${window.location.origin}/auth/callback`,
          },
        });

        if (error) {
          logger.error('OAuth sign in failed', error, { provider });
          throw error;
        }
      } catch (error) {
        logger.error('OAuth sign in error', error as Error, { provider });
        throw error;
      }
    },
    [supabase.auth]
  );

  /**
   * Refresh session manually
   */
  const refreshSession = useCallback(async () => {
    try {
      const { data, error } = await supabase.auth.refreshSession();
      if (error) {
        logger.error('Session refresh failed', error);
        throw error;
      }
      if (data.session) {
        setSession(data.session);
        setUser(data.session.user);
      }
    } catch (error) {
      logger.error('Session refresh error', error as Error);
      throw error;
    }
  }, [supabase.auth]);

  const value: AuthContextType = {
    user,
    session,
    loading,
    signIn,
    signUp,
    signOut,
    signInWithOAuth,
    refreshSession,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

/**
 * Hook to use auth context
 */
export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

/**
 * Hook to get current user
 */
export function useUser(): User | null {
  const { user } = useAuth();
  return user;
}

/**
 * Hook to get current session
 */
export function useSession(): Session | null {
  const { session } = useAuth();
  return session;
}
