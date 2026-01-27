/**
 * URL Utilities
 * 
 * Helper functions for constructing URLs with proper protocol handling
 */

/**
 * Get the app URL with proper protocol
 * In development, ensures HTTPS is used
 */
export function getAppUrl(): string {
  const appUrl = process.env.NEXT_PUBLIC_APP_URL || 'https://localhost:3000'
  
  // In development, ensure HTTPS is used
  if (process.env.NODE_ENV === 'development' && appUrl.startsWith('http://')) {
    return appUrl.replace('http://', 'https://')
  }
  
  return appUrl
}

/**
 * Create a URL for a given path using the app URL
 */
export function createAppUrl(path: string): URL {
  const appUrl = getAppUrl()
  return new URL(path, appUrl)
}
