/**
 * Error Handler Middleware
 * 
 * Provides error handling for Next.js API routes and server components.
 */

import { NextRequest, NextResponse } from 'next/server';
import { BaseError, ErrorContext } from './base';
import { ErrorCodes } from './error-codes';
import { logger, generateRequestId } from './logger';

/**
 * Sanitize error for user-facing responses
 * Removes sensitive information and stack traces
 */
function sanitizeError(error: BaseError): {
  message: string;
  code: string;
  type: string;
  retryable: boolean;
  context: ErrorContext;
} {
  // Create sanitized context (remove sensitive data)
  const sanitizedContext: ErrorContext = {
    ...error.context,
  };

  // Remove sensitive fields
  delete sanitizedContext.password;
  delete sanitizedContext.token;
  delete sanitizedContext.secret;
  delete sanitizedContext.apiKey;

  return {
    message: error.getUserMessage(),
    code: error.code,
    type: error.type,
    retryable: error.retryable,
    context: sanitizedContext,
  };
}

/**
 * Handle error and return appropriate response
 */
export function handleError(error: unknown, requestId?: string): NextResponse {
  // Log the error with full details
  if (error instanceof BaseError) {
    logger.error('Error occurred', error, { requestId });
  } else if (error instanceof Error) {
    logger.error('Unexpected error occurred', error, { requestId });
  } else {
    // Handle non-Error objects (e.g., Supabase errors, plain objects)
    const errorMessage = 
      error && typeof error === 'object' && 'message' in error
        ? String(error.message)
        : error && typeof error === 'object' && 'error' in error
        ? String(error.error)
        : String(error);
    
    logger.error('Unknown error occurred', undefined, {
      requestId,
      error: errorMessage,
      errorObject: error,
    });
  }

  // Convert to BaseError if needed
  let baseError: BaseError;

  if (error instanceof BaseError) {
    baseError = error;
  } else if (error instanceof Error) {
    // Convert unknown errors to system error
    baseError = new BaseError(
      ErrorCodes.SYSTEM_UNKNOWN_ERROR,
      'An unexpected error occurred',
      { requestId },
      error
    );
  } else {
    // Handle non-Error objects (e.g., Supabase errors, plain objects)
    const errorMessage = 
      error && typeof error === 'object' && 'message' in error
        ? String(error.message)
        : error && typeof error === 'object' && 'error' in error
        ? String(error.error)
        : 'An unknown error occurred';
    
    baseError = new BaseError(
      ErrorCodes.SYSTEM_UNKNOWN_ERROR,
      errorMessage,
      { 
        requestId,
        originalError: error && typeof error === 'object' ? JSON.stringify(error) : String(error)
      }
    );
  }

  // Sanitize error for response
  const sanitized = sanitizeError(baseError);

  // Return error response
  return NextResponse.json(
    {
      error: sanitized,
    },
    {
      status: baseError.statusCode,
      headers: {
        'X-Request-ID': requestId || generateRequestId(),
      },
    }
  );
}

/**
 * Error handler middleware for Next.js API routes
 */
export function withErrorHandler(
  handler: (req: NextRequest, context?: unknown) => Promise<NextResponse>
) {
  return async (req: NextRequest, context?: unknown): Promise<NextResponse> => {
    const requestId = req.headers.get('x-request-id') || generateRequestId();

    try {
      // Set request ID in logger context
      logger.setContext({ requestId });

      // Execute handler
      const response = await handler(req, context);

      // Add request ID to response headers
      response.headers.set('X-Request-ID', requestId);

      return response;
    } catch (error) {
      return handleError(error, requestId);
    } finally {
      // Clear logger context
      logger.clearContext();
    }
  };
}

/**
 * Create error response
 */
export function createErrorResponse(
  error: BaseError,
  requestId?: string
): NextResponse {
  const sanitized = sanitizeError(error);

  return NextResponse.json(
    {
      error: sanitized,
    },
    {
      status: error.statusCode,
      headers: {
        'X-Request-ID': requestId || generateRequestId(),
      },
    }
  );
}

/**
 * Extract request ID from request
 */
export function getRequestId(req: NextRequest): string {
  return req.headers.get('x-request-id') || generateRequestId();
}
