/**
 * Base Error Classes
 * 
 * Provides base error class and specific error types for the application.
 */

import { ErrorCode, ErrorCodes, ErrorCodeMetadataMap, getErrorCodeMetadata } from './error-codes';

/**
 * Error context for additional error information
 */
export interface ErrorContext {
  requestId?: string;
  userId?: string;
  appId?: string;
  field?: string;
  details?: Record<string, unknown>;
  [key: string]: unknown;
}

/**
 * Base Error Class
 * 
 * All application errors extend this class.
 */
export class BaseError extends Error {
  public readonly code: ErrorCode;
  public readonly type: string;
  public readonly statusCode: number;
  public readonly retryable: boolean;
  public readonly context: ErrorContext;
  public readonly originalError?: Error;
  public readonly timestamp: Date;

  constructor(
    code: ErrorCode,
    message?: string,
    context: ErrorContext = {},
    originalError?: Error
  ) {
    const metadata = getErrorCodeMetadata(code);
    const userMessage = message || metadata.userMessage;

    super(userMessage);

    this.name = this.constructor.name;
    this.code = code;
    this.type = metadata.category.toLowerCase();
    this.statusCode = metadata.httpStatus;
    this.retryable = metadata.retryable;
    this.context = context;
    this.originalError = originalError;
    this.timestamp = new Date();

    // Maintains proper stack trace for where our error was thrown (only available on V8)
    if (Error.captureStackTrace) {
      Error.captureStackTrace(this, this.constructor);
    }
  }

  /**
   * Convert error to JSON for API responses
   */
  toJSON() {
    return {
      error: {
        message: this.message,
        code: this.code,
        type: this.type,
        retryable: this.retryable,
        context: this.context,
      },
    };
  }

  /**
   * Get user-friendly error message
   */
  getUserMessage(): string {
    return this.message;
  }
}

/**
 * Transient Error (Retryable)
 * 
 * Errors that may succeed on retry (network issues, rate limits, etc.)
 */
export class TransientError extends BaseError {
  constructor(
    code: ErrorCode,
    message?: string,
    context: ErrorContext = {},
    originalError?: Error
  ) {
    super(code, message, context, originalError);
  }
}

/**
 * Permanent Error (Not Retryable)
 * 
 * Errors that won't succeed on retry (validation, auth, etc.)
 */
export class PermanentError extends BaseError {
  constructor(
    code: ErrorCode,
    message?: string,
    context: ErrorContext = {},
    originalError?: Error
  ) {
    super(code, message, context, originalError);
  }
}

/**
 * System Error (Infrastructure)
 * 
 * Errors related to system/infrastructure issues
 */
export class SystemError extends BaseError {
  constructor(
    code: ErrorCode,
    message?: string,
    context: ErrorContext = {},
    originalError?: Error
  ) {
    super(code, message, context, originalError);
  }
}

/**
 * Validation Error
 * 
 * Input validation errors
 */
export class ValidationError extends PermanentError {
  constructor(
    message: string,
    context: ErrorContext = {},
    originalError?: Error
  ) {
    super(ErrorCodes.PERMANENT_VALIDATION_ERROR, message, context, originalError);
  }
}

/**
 * Authentication Error
 * 
 * Authentication failures
 */
export class AuthenticationError extends PermanentError {
  constructor(
    message?: string,
    context: ErrorContext = {},
    originalError?: Error
  ) {
    super(
      ErrorCodes.PERMANENT_AUTHENTICATION_ERROR,
      message || 'Authentication failed',
      context,
      originalError
    );
  }
}

/**
 * Authorization Error
 * 
 * Permission/authorization failures
 */
export class AuthorizationError extends PermanentError {
  constructor(
    message?: string,
    context: ErrorContext = {},
    originalError?: Error
  ) {
    super(
      ErrorCodes.PERMANENT_AUTHORIZATION_ERROR,
      message || 'Authorization failed',
      context,
      originalError
    );
  }
}

/**
 * Not Found Error
 * 
 * Resource not found errors
 */
export class NotFoundError extends PermanentError {
  constructor(
    resource?: string,
    context: ErrorContext = {},
    originalError?: Error
  ) {
    const message = resource ? `${resource} not found` : 'Resource not found';
    super(ErrorCodes.PERMANENT_NOT_FOUND_ERROR, message, context, originalError);
  }
}

/**
 * Database Error
 * 
 * Database operation errors
 */
export class DatabaseError extends SystemError {
  constructor(
    message?: string,
    context: ErrorContext = {},
    originalError?: Error
  ) {
    super(
      ErrorCodes.SYSTEM_DATABASE_ERROR,
      message || 'Database error occurred',
      context,
      originalError
    );
  }
}

/**
 * Network Error
 * 
 * Network-related errors
 */
export class NetworkError extends TransientError {
  constructor(
    message?: string,
    context: ErrorContext = {},
    originalError?: Error
  ) {
    super(
      ErrorCodes.TRANSIENT_NETWORK_ERROR,
      message || 'Network error occurred',
      context,
      originalError
    );
  }
}

/**
 * Rate Limit Error
 * 
 * Rate limit exceeded errors
 */
export class RateLimitError extends TransientError {
  constructor(
    message?: string,
    context: ErrorContext = {},
    originalError?: Error
  ) {
    super(
      ErrorCodes.TRANSIENT_RATE_LIMIT_ERROR,
      message || 'Rate limit exceeded',
      context,
      originalError
    );
  }
}
