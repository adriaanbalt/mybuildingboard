"""
Error Handling Utilities

Error handling and formatting for the API.
"""

from fastapi import Request
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger(__name__)


def handle_error(error: Exception, request: Request) -> JSONResponse:
    """
    Handle errors and return formatted error response.
    
    Args:
        error: Exception that occurred
        request: FastAPI request object
        
    Returns:
        JSON error response
    """
    logger.error(f"Unhandled error: {error}", exc_info=True)
    
    # Determine status code based on error type
    status_code = 500
    error_code = "INTERNAL_ERROR"
    
    if isinstance(error, ValueError):
        status_code = 400
        error_code = "VALIDATION_ERROR"
    elif isinstance(error, PermissionError):
        status_code = 403
        error_code = "PERMISSION_DENIED"
    elif isinstance(error, FileNotFoundError):
        status_code = 404
        error_code = "NOT_FOUND"
    
    return JSONResponse(
        status_code=status_code,
        content={
            "error": str(error),
            "error_code": error_code,
            "details": {
                "path": request.url.path,
                "method": request.method,
            }
        }
    )
