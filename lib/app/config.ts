/**
 * App Configuration System
 *
 * Loads and caches app configuration from database.
 */

import { createServerSupabaseClient } from '@/lib/auth/server'
import type { App, AppConfig, AppWithConfig } from './types'

/**
 * In-memory cache for app configs
 * Key: app_id, Value: { app, config, timestamp }
 */
const configCache = new Map<
  string,
  {
    app: App
    config: AppConfig['config'] | null
    timestamp: number
  }
>()

const CACHE_TTL = 5 * 60 * 1000 // 5 minutes

/**
 * Load app from database
 */
async function loadAppFromDatabase(appId: string): Promise<App | null> {
  const supabase = await createServerSupabaseClient()
  const { data, error } = await supabase
    .from('apps')
    .select('id, name, subdomain, created_at, updated_at')
    .eq('id', appId as any)
    .single()

  if (error || !data) {
    return null
  }

  return data as App
}

/**
 * Load app config from database
 */
async function loadAppConfigFromDatabase(appId: string): Promise<AppConfig['config'] | null> {
  const supabase = await createServerSupabaseClient()
  const { data, error } = await supabase
    .from('app_configs')
    .select('config')
    .eq('app_id', appId as any)
    .single()

  if (error || !data) {
    return null
  }

  return (data as any).config
}

/**
 * Get app configuration (with caching)
 *
 * @param appId - App ID
 * @param useCache - Whether to use cache (default: true)
 * @returns App with config or null if not found
 */
export async function getAppConfig(
  appId: string,
  useCache: boolean = true
): Promise<AppWithConfig | null> {
  // Check cache first
  if (useCache) {
    const cached = configCache.get(appId)
    if (cached && Date.now() - cached.timestamp < CACHE_TTL) {
      return {
        ...cached.app,
        config: cached.config || undefined,
      }
    }
  }

  // Load from database
  const app = await loadAppFromDatabase(appId)
  if (!app) {
    return null
  }

  const config = await loadAppConfigFromDatabase(appId)

  // Update cache
  if (useCache) {
    configCache.set(appId, {
      app,
      config,
      timestamp: Date.now(),
    })
  }

  return {
    ...app,
    config: config || {},
  }
}

/**
 * Invalidate app config cache
 */
export function invalidateAppConfigCache(appId: string): void {
  configCache.delete(appId)
}

/**
 * Clear all app config cache
 */
export function clearAppConfigCache(): void {
  configCache.clear()
}

/**
 * Get app by ID (without config)
 */
export async function getApp(appId: string): Promise<App | null> {
  const appConfig = await getAppConfig(appId)
  if (!appConfig) {
    return null
  }

  return {
    id: appConfig.id,
    name: appConfig.name,
    subdomain: appConfig.subdomain,
    created_at: appConfig.created_at,
    updated_at: appConfig.updated_at,
  }
}
