/**
 * Error Code Registry
 * 
 * Defines all error codes used throughout the application.
 * Format: CATEGORY_TYPE_DESCRIPTION (e.g., TRANSIENT_NETWORK_ERROR)
 */

export enum ErrorCategory {
  TRANSIENT = 'TRANSIENT',
  PERMANENT = 'PERMANENT',
  SYSTEM = 'SYSTEM',
}

export enum ErrorType {
  NETWORK = 'NETWORK',
  RATE_LIMIT = 'RATE_LIMIT',
  SERVICE_UNAVAILABLE = 'SERVICE_UNAVAILABLE',
  DATABASE = 'DATABASE',
  VALIDATION = 'VALIDATION',
  AUTHENTICATION = 'AUTHENTICATION',
  AUTHORIZATION = 'AUTHORIZATION',
  NOT_FOUND = 'NOT_FOUND',
  CONFIGURATION = 'CONFIGURATION',
  UNKNOWN = 'UNKNOWN',
}

/**
 * Error Code Registry
 * 
 * All error codes follow the format: CATEGORY_TYPE_DESCRIPTION
 */
export const ErrorCodes = {
  // TRANSIENT Errors (Retryable)
  TRANSIENT_NETWORK_ERROR: 'TRANSIENT_NETWORK_ERROR',
  TRANSIENT_RATE_LIMIT_ERROR: 'TRANSIENT_RATE_LIMIT_ERROR',
  TRANSIENT_SERVICE_UNAVAILABLE: 'TRANSIENT_SERVICE_UNAVAILABLE',
  TRANSIENT_DATABASE_CONNECTION_ERROR: 'TRANSIENT_DATABASE_CONNECTION_ERROR',
  TRANSIENT_TIMEOUT_ERROR: 'TRANSIENT_TIMEOUT_ERROR',

  // PERMANENT Errors (Not Retryable)
  PERMANENT_VALIDATION_ERROR: 'PERMANENT_VALIDATION_ERROR',
  PERMANENT_AUTHENTICATION_ERROR: 'PERMANENT_AUTHENTICATION_ERROR',
  PERMANENT_AUTHORIZATION_ERROR: 'PERMANENT_AUTHORIZATION_ERROR',
  PERMANENT_NOT_FOUND_ERROR: 'PERMANENT_NOT_FOUND_ERROR',
  PERMANENT_INVALID_INPUT_ERROR: 'PERMANENT_INVALID_INPUT_ERROR',
  PERMANENT_DUPLICATE_RESOURCE_ERROR: 'PERMANENT_DUPLICATE_RESOURCE_ERROR',

  // SYSTEM Errors (Infrastructure)
  SYSTEM_DATABASE_ERROR: 'SYSTEM_DATABASE_ERROR',
  SYSTEM_CONFIGURATION_ERROR: 'SYSTEM_CONFIGURATION_ERROR',
  SYSTEM_MISSING_ENV_VAR_ERROR: 'SYSTEM_MISSING_ENV_VAR_ERROR',
  SYSTEM_SERVICE_UNAVAILABLE: 'SYSTEM_SERVICE_UNAVAILABLE',
  SYSTEM_INTERNAL_ERROR: 'SYSTEM_INTERNAL_ERROR',
  SYSTEM_UNKNOWN_ERROR: 'SYSTEM_UNKNOWN_ERROR',
} as const;

export type ErrorCode = typeof ErrorCodes[keyof typeof ErrorCodes];

/**
 * Error Code Metadata
 * Maps error codes to their category, type, HTTP status, and retry policy
 */
export interface ErrorCodeMetadata {
  category: ErrorCategory;
  type: ErrorType;
  httpStatus: number;
  retryable: boolean;
  userMessage: string;
}

export const ErrorCodeMetadataMap: Record<ErrorCode, ErrorCodeMetadata> = {
  // TRANSIENT Errors
  [ErrorCodes.TRANSIENT_NETWORK_ERROR]: {
    category: ErrorCategory.TRANSIENT,
    type: ErrorType.NETWORK,
    httpStatus: 503,
    retryable: true,
    userMessage: 'Network error occurred. Please try again.',
  },
  [ErrorCodes.TRANSIENT_RATE_LIMIT_ERROR]: {
    category: ErrorCategory.TRANSIENT,
    type: ErrorType.RATE_LIMIT,
    httpStatus: 429,
    retryable: true,
    userMessage: 'Rate limit exceeded. Please try again later.',
  },
  [ErrorCodes.TRANSIENT_SERVICE_UNAVAILABLE]: {
    category: ErrorCategory.TRANSIENT,
    type: ErrorType.SERVICE_UNAVAILABLE,
    httpStatus: 503,
    retryable: true,
    userMessage: 'Service temporarily unavailable. Please try again later.',
  },
  [ErrorCodes.TRANSIENT_DATABASE_CONNECTION_ERROR]: {
    category: ErrorCategory.TRANSIENT,
    type: ErrorType.DATABASE,
    httpStatus: 503,
    retryable: true,
    userMessage: 'Database connection error. Please try again.',
  },
  [ErrorCodes.TRANSIENT_TIMEOUT_ERROR]: {
    category: ErrorCategory.TRANSIENT,
    type: ErrorType.NETWORK,
    httpStatus: 504,
    retryable: true,
    userMessage: 'Request timeout. Please try again.',
  },

  // PERMANENT Errors
  [ErrorCodes.PERMANENT_VALIDATION_ERROR]: {
    category: ErrorCategory.PERMANENT,
    type: ErrorType.VALIDATION,
    httpStatus: 400,
    retryable: false,
    userMessage: 'Validation error. Please check your input.',
  },
  [ErrorCodes.PERMANENT_AUTHENTICATION_ERROR]: {
    category: ErrorCategory.PERMANENT,
    type: ErrorType.AUTHENTICATION,
    httpStatus: 401,
    retryable: false,
    userMessage: 'Authentication failed. Please log in again.',
  },
  [ErrorCodes.PERMANENT_AUTHORIZATION_ERROR]: {
    category: ErrorCategory.PERMANENT,
    type: ErrorType.AUTHORIZATION,
    httpStatus: 403,
    retryable: false,
    userMessage: 'You do not have permission to perform this action.',
  },
  [ErrorCodes.PERMANENT_NOT_FOUND_ERROR]: {
    category: ErrorCategory.PERMANENT,
    type: ErrorType.NOT_FOUND,
    httpStatus: 404,
    retryable: false,
    userMessage: 'Resource not found.',
  },
  [ErrorCodes.PERMANENT_INVALID_INPUT_ERROR]: {
    category: ErrorCategory.PERMANENT,
    type: ErrorType.VALIDATION,
    httpStatus: 400,
    retryable: false,
    userMessage: 'Invalid input provided.',
  },
  [ErrorCodes.PERMANENT_DUPLICATE_RESOURCE_ERROR]: {
    category: ErrorCategory.PERMANENT,
    type: ErrorType.VALIDATION,
    httpStatus: 409,
    retryable: false,
    userMessage: 'Resource already exists.',
  },

  // SYSTEM Errors
  [ErrorCodes.SYSTEM_DATABASE_ERROR]: {
    category: ErrorCategory.SYSTEM,
    type: ErrorType.DATABASE,
    httpStatus: 500,
    retryable: true,
    userMessage: 'Database error occurred. Please contact support.',
  },
  [ErrorCodes.SYSTEM_CONFIGURATION_ERROR]: {
    category: ErrorCategory.SYSTEM,
    type: ErrorType.CONFIGURATION,
    httpStatus: 500,
    retryable: false,
    userMessage: 'System configuration error. Please contact support.',
  },
  [ErrorCodes.SYSTEM_MISSING_ENV_VAR_ERROR]: {
    category: ErrorCategory.SYSTEM,
    type: ErrorType.CONFIGURATION,
    httpStatus: 500,
    retryable: false,
    userMessage: 'System configuration error. Please contact support.',
  },
  [ErrorCodes.SYSTEM_SERVICE_UNAVAILABLE]: {
    category: ErrorCategory.SYSTEM,
    type: ErrorType.SERVICE_UNAVAILABLE,
    httpStatus: 503,
    retryable: true,
    userMessage: 'Service unavailable. Please try again later.',
  },
  [ErrorCodes.SYSTEM_INTERNAL_ERROR]: {
    category: ErrorCategory.SYSTEM,
    type: ErrorType.UNKNOWN,
    httpStatus: 500,
    retryable: false,
    userMessage: 'An internal error occurred. Please contact support.',
  },
  [ErrorCodes.SYSTEM_UNKNOWN_ERROR]: {
    category: ErrorCategory.SYSTEM,
    type: ErrorType.UNKNOWN,
    httpStatus: 500,
    retryable: false,
    userMessage: 'An unexpected error occurred. Please contact support.',
  },
};

/**
 * Get error code metadata
 */
export function getErrorCodeMetadata(code: ErrorCode): ErrorCodeMetadata {
  return ErrorCodeMetadataMap[code];
}
