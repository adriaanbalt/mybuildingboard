/**
 * TLS Configuration Utility for Local Development
 *
 * Handles self-signed certificate acceptance for local HTTPS development.
 * This is only enabled in development when connecting to localhost/127.0.0.1.
 *
 * NOTE: Setting NODE_TLS_REJECT_UNAUTHORIZED will trigger a Node.js warning.
 * This is expected behavior in development and can be safely ignored.
 */

let tlsConfigured = false

/**
 * Configure Node.js to accept self-signed certificates for local development.
 * This should be called before making HTTPS requests to local Supabase or other local services.
 *
 * Only applies in development mode when connecting to localhost/127.0.0.1.
 *
 * The warning "Setting the NODE_TLS_REJECT_UNAUTHORIZED environment variable to '0'..."
 * is expected in development and can be safely ignored.
 *
 * @param url - The URL being connected to (optional, for validation)
 */
export function configureLocalTLS(url?: string): void {
  // Only configure in development
  if (process.env.NODE_ENV !== 'development') {
    return
  }

  // Only configure if connecting to localhost
  if (url) {
    const isLocal = url.includes('127.0.0.1') || url.includes('localhost')
    if (!isLocal) {
      return
    }
  }

  // Only set once to avoid multiple warnings
  // Check if already set to avoid redundant configuration
  if (tlsConfigured || process.env.NODE_TLS_REJECT_UNAUTHORIZED === '0') {
    return
  }

  // Set the environment variable
  // This will trigger a Node.js warning, which is expected in development
  // Note: In Edge runtime (production middleware), process.env might be read-only
  // This is safe to ignore as Edge runtime doesn't use Node.js TLS
  try {
    process.env.NODE_TLS_REJECT_UNAUTHORIZED = '0'
    tlsConfigured = true
  } catch (error) {
    // In Edge runtime, process.env might be read-only - this is fine
    // Edge runtime uses fetch API which handles TLS differently
  }
}

/**
 * Check if a URL requires local TLS configuration
 */
export function requiresLocalTLS(url: string): boolean {
  if (process.env.NODE_ENV !== 'development') {
    return false
  }

  const isLocal = url.includes('127.0.0.1') || url.includes('localhost')
  const isHttps = url.startsWith('https://')

  return isLocal && isHttps
}
