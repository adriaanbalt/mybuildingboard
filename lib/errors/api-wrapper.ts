/**
 * API Wrapper Functions
 *
 * Provides wrapper functions for Next.js API routes with automatic error handling.
 */

import { NextRequest, NextResponse } from 'next/server'
import { withErrorHandler, getRequestId } from './handlers'
import { logger } from './logger'

/**
 * API Handler function type
 * Matches Next.js App Router route handler signature where context is always provided
 */
export type ApiHandler<T = unknown> = (req: NextRequest, context: T) => Promise<NextResponse>

/**
 * API Route wrapper with automatic error handling
 *
 * Usage:
 * ```ts
 * // Without params (use empty object):
 * export const GET = apiHandler(async (req, _context) => {
 *   return NextResponse.json({ data: 'success' });
 * });
 *
 * // With params:
 * export const GET = apiHandler(async (req, { params }) => {
 *   const { id } = params;
 *   return NextResponse.json({ id });
 * });
 * ```
 */
export function apiHandler<T = unknown>(
  handler: ApiHandler<T>
): (req: NextRequest, context: T) => Promise<NextResponse> {
  // Return a function that matches Next.js route handler signature
  // Next.js always provides context, but we need to handle the case where
  // it might be undefined for backward compatibility
  return async (req: NextRequest, context: T): Promise<NextResponse> => {
    const requestId = getRequestId(req)

    // Set request ID in logger context
    logger.setContext({ requestId })

    try {
      // Wrap handler with error handling
      return await withErrorHandler(async (req: NextRequest, context?: unknown) => {
        // Context is always provided by Next.js for route handlers
        return await handler(req, (context ?? {}) as T)
      })(req, context)
    } finally {
      // Clear logger context
      logger.clearContext()
    }
  }
}

/**
 * API Route wrapper with request ID extraction
 *
 * Extracts and sets request ID from headers or generates a new one.
 */
export function withRequestId<T = unknown>(
  handler: (req: NextRequest, context?: T, requestId?: string) => Promise<NextResponse>
): ApiHandler<T> {
  return apiHandler(async (req: NextRequest, context?: T) => {
    const requestId = getRequestId(req)
    return handler(req, context, requestId)
  })
}
