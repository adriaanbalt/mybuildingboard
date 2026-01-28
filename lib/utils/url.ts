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
 * Edge runtime compatible - uses request origin as fallback
 */
export function createAppUrl(path: string, origin?: string): URL {
  try {
    const appUrl = getAppUrl()
    // Validate URL is valid
    if (appUrl && (appUrl.startsWith('http://') || appUrl.startsWith('https://'))) {
      return new URL(path, appUrl)
    }
    // If appUrl is invalid, use origin if provided
    if (origin) {
      return new URL(path, origin)
    }
    // Last resort fallback
    return new URL(path, 'https://localhost:3000')
  } catch (error) {
    // Fallback if URL construction fails
    // Use origin from request if available
    if (origin) {
      try {
        return new URL(path, origin)
      } catch {
        // If that also fails, use default
      }
    }
    // Return a safe fallback URL
    return new URL(path, 'https://localhost:3000')
  }
}
