/**
 * API Wrapper Functions
 * 
 * Provides wrapper functions for Next.js API routes with automatic error handling.
 */

import { NextRequest, NextResponse } from 'next/server';
import { withErrorHandler, getRequestId } from './handlers';
import { logger } from './logger';

/**
 * API Handler function type
 */
export type ApiHandler<T = unknown> = (
  req: NextRequest,
  context?: T
) => Promise<NextResponse>;

/**
 * API Route wrapper with automatic error handling
 * 
 * Usage:
 * ```ts
 * export const GET = apiHandler(async (req) => {
 *   // Your route logic here
 *   return NextResponse.json({ data: 'success' });
 * });
 * ```
 */
export function apiHandler<T = unknown>(
  handler: ApiHandler<T>
): ApiHandler<T> {
  return withErrorHandler(async (req: NextRequest, context?: T) => {
    const requestId = getRequestId(req);

    // Set request ID in logger context
    logger.setContext({ requestId });

    try {
      // Execute handler
      const response = await handler(req, context);

      // Add request ID to response headers if not already present
      if (!response.headers.get('X-Request-ID')) {
        response.headers.set('X-Request-ID', requestId);
      }

      return response;
    } finally {
      // Clear logger context
      logger.clearContext();
    }
  });
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
    const requestId = getRequestId(req);
    return handler(req, context, requestId);
  });
}
