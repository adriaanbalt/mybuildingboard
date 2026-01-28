/**
 * URL Utilities
 *
 * Helper functions for constructing URLs with proper protocol handling
 */

/**
 * Get the app URL with proper protocol
 * In development, ensures HTTPS is used
 * Edge runtime compatible - checks process.env at runtime
 */
export function getAppUrl(): string {
  // Edge runtime compatible - check process.env at runtime
  let appUrl: string | undefined
  if (typeof process !== 'undefined' && process.env) {
    appUrl = process.env.NEXT_PUBLIC_APP_URL
  }

  // Fallback for Edge runtime or missing env var
  if (!appUrl) {
    // Try to get from request headers in middleware context
    // For production, use a sensible default
    appUrl = 'https://localhost:3000'
  }

  // In development, ensure HTTPS is used
  if (
    typeof process !== 'undefined' &&
    process.env &&
    process.env.NODE_ENV === 'development' &&
    appUrl.startsWith('http://')
  ) {
    return appUrl.replace('http://', 'https://')
  }

  return appUrl
}

/**
 * Create a URL for a given path using the app URL
 * Edge runtime compatible
 */
export function createAppUrl(path: string): URL {
  try {
    const appUrl = getAppUrl()
    return new URL(path, appUrl)
  } catch (error) {
    // Fallback if URL construction fails
    // This can happen in Edge runtime with invalid URLs
    console.error('[createAppUrl] Failed to create URL:', error)
    // Return a safe fallback URL
    return new URL(path, 'https://localhost:3000')
  }
}
