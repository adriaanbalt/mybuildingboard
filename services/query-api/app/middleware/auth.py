"""
Authentication Middleware

Supabase JWT validation and user context extraction.
"""

import os
import logging
from typing import Optional
from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from supabase import create_client, Client
import jwt

logger = logging.getLogger(__name__)
security = HTTPBearer()

# Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET")

if not SUPABASE_URL or not SUPABASE_JWT_SECRET:
    raise ValueError("SUPABASE_URL and SUPABASE_JWT_SECRET must be set")


def get_supabase_client() -> Client:
    """Get Supabase client."""
    from supabase import create_client
    return create_client(SUPABASE_URL, SUPABASE_JWT_SECRET)


async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """
    Verify Supabase JWT token and extract user information.
    
    Args:
        credentials: HTTP Bearer token credentials
        
    Returns:
        Decoded JWT payload with user information
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    token = credentials.credentials
    
    try:
        # Decode JWT token (Supabase uses HS256)
        # In production, verify with Supabase's public key
        payload = jwt.decode(
            token,
            SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            options={"verify_signature": True}
        )
        
        # Extract user information
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token: missing user ID")
        
        return {
            "user_id": user_id,
            "email": payload.get("email"),
            "app_metadata": payload.get("app_metadata", {}),
            "user_metadata": payload.get("user_metadata", {}),
        }
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Token verification failed: {str(e)}")


def get_app_id_from_request(request: Request, user_context: dict) -> Optional[str]:
    """
    Extract app_id from request (header, JWT, or body).
    
    Priority:
    1. x-app-id header
    2. JWT token claims (app_id)
    3. Request body (if available)
    
    Args:
        request: FastAPI request
        user_context: User context from JWT
        
    Returns:
        App ID or None
    """
    # Check header first
    app_id = request.headers.get("x-app-id")
    if app_id:
        return app_id
    
    # Check JWT claims
    app_id = user_context.get("app_metadata", {}).get("app_id")
    if app_id:
        return app_id
    
    return None


async def verify_app_membership(
    user_id: str,
    app_id: str,
    supabase: Client
) -> bool:
    """
    Verify user is a member of the app.
    
    Args:
        user_id: User ID
        app_id: App ID
        supabase: Supabase client
        
    Returns:
        True if user is a member, False otherwise
    """
    try:
        result = supabase.table("app_members").select("*").eq("app_id", app_id).eq("user_id", user_id).execute()
        return len(result.data) > 0
    except Exception as e:
        logger.error(f"Failed to verify app membership: {e}")
        return False


async def require_auth(request: Request, credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """
    Dependency for protected routes - requires authentication.
    
    Returns:
        User context dictionary
    """
    return await verify_token(credentials)


async def require_app_membership(
    request: Request,
    user_context: dict = Depends(require_auth)
) -> tuple[str, str]:
    """
    Dependency for routes that require app membership.
    
    Returns:
        Tuple of (user_id, app_id)
    """
    user_id = user_context["user_id"]
    app_id = get_app_id_from_request(request, user_context)
    
    if not app_id:
        raise HTTPException(
            status_code=400,
            detail="app_id is required. Provide it in x-app-id header or JWT token."
        )
    
    # Verify app membership
    supabase = get_supabase_client()
    if not await verify_app_membership(user_id, app_id, supabase):
        raise HTTPException(
            status_code=403,
            detail=f"User is not a member of app {app_id}"
        )
    
    return user_id, app_id
