'use client';

/**
 * AppContext Provider
 * 
 * Provides app context (app_id, app config) throughout the application.
 */

import React, { createContext, useContext, useEffect, useState, useCallback } from 'react';
import { useAuth } from './AuthContext';
import type { AppWithConfig } from '@/lib/app/types';

interface AppContextType {
  appId: string | null;
  app: AppWithConfig | null;
  loading: boolean;
  setAppId: (appId: string | null) => void;
  refreshApp: () => Promise<void>;
}

const AppContext = createContext<AppContextType | undefined>(undefined);

export function AppProvider({ children }: { children: React.ReactNode }) {
  const { user } = useAuth();
  const [appId, setAppIdState] = useState<string | null>(null);
  const [app, setApp] = useState<AppWithConfig | null>(null);
  const [loading, setLoading] = useState(true);

  /**
   * Load app ID from cookie on mount
   */
  useEffect(() => {
    if (typeof window === 'undefined') return;

    const cookieAppId = document.cookie
      .split('; ')
      .find((row) => row.startsWith('app_id='))
      ?.split('=')[1];

    if (cookieAppId) {
      setAppIdState(cookieAppId);
    } else {
      // If no cookie, try to get from user's memberships
      // This will be handled by middleware, but we can also fetch here
      setLoading(false);
    }
  }, []);

  /**
   * Load app config when appId changes
   */
  useEffect(() => {
    if (!appId || !user) {
      setApp(null);
      setLoading(false);
      return;
    }

    const loadApp = async () => {
      setLoading(true);
      try {
        const response = await fetch(`/api/app/${appId}`);
        if (response.ok) {
          const appData = await response.json();
          setApp(appData);
        } else {
          setApp(null);
        }
      } catch (error) {
        console.error('Failed to load app config:', error);
        setApp(null);
      } finally {
        setLoading(false);
      }
    };

    loadApp();
  }, [appId, user]);

  /**
   * Set app ID and update cookie
   */
  const setAppId = useCallback((newAppId: string | null) => {
    setAppIdState(newAppId);

    if (typeof window !== 'undefined') {
      if (newAppId) {
        // Set cookie (expires in 1 year)
        document.cookie = `app_id=${newAppId}; path=/; max-age=${365 * 24 * 60 * 60}`;
      } else {
        // Remove cookie
        document.cookie = 'app_id=; path=/; max-age=0';
      }
    }
  }, []);

  /**
   * Refresh app config
   */
  const refreshApp = useCallback(async () => {
    if (!appId) return;

    setLoading(true);
    try {
      const response = await fetch(`/api/app/${appId}`);
      if (response.ok) {
        const appData = await response.json();
        setApp(appData);
      }
    } catch (error) {
      console.error('Failed to refresh app config:', error);
    } finally {
      setLoading(false);
    }
  }, [appId]);

  const value: AppContextType = {
    appId,
    app,
    loading,
    setAppId,
    refreshApp,
  };

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
}

/**
 * Hook to use app context
 */
export function useApp(): AppContextType {
  const context = useContext(AppContext);
  if (context === undefined) {
    throw new Error('useApp must be used within an AppProvider');
  }
  return context;
}

/**
 * Hook to get current app ID
 */
export function useAppId(): string | null {
  const { appId } = useApp();
  return appId;
}

/**
 * Hook to get current app config
 */
export function useAppConfig(): AppWithConfig | null {
  const { app } = useApp();
  return app;
}

/**
 * Hook to get app membership status
 */
export function useAppMembership() {
  const { appId } = useApp();
  const { user } = useAuth();
  const [membership, setMembership] = useState<{
    isMember: boolean;
    role: 'owner' | 'admin' | 'member' | null;
    loading: boolean;
  }>({
    isMember: false,
    role: null,
    loading: true,
  });

  useEffect(() => {
    if (!appId || !user) {
      setMembership({ isMember: false, role: null, loading: false });
      return;
    }

    const checkMembership = async () => {
      setMembership((prev) => ({ ...prev, loading: true }));
      try {
        const response = await fetch(`/api/app/${appId}/membership`);
        if (response.ok) {
          const data = await response.json();
          setMembership({
            isMember: data.isMember,
            role: data.role,
            loading: false,
          });
        } else {
          setMembership({ isMember: false, role: null, loading: false });
        }
      } catch (error) {
        console.error('Failed to check membership:', error);
        setMembership({ isMember: false, role: null, loading: false });
      }
    };

    checkMembership();
  }, [appId, user]);

  return membership;
}
