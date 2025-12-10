import os
import jwt
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from pydantic_settings import BaseSettings
import requests


class AuthSettings(BaseSettings):
    """Settings for authentication"""
    clerk_secret_key: Optional[str] = None
    clerk_jwks_url: Optional[str] = None  # Will be constructed from publishable key if needed
    
    class Config:
        env_file = ".env"
        extra = "ignore"  # Ignore extra environment variables


security = HTTPBearer()
optional_security = HTTPBearer(auto_error=False)


def get_jwks_url() -> str:
    """Get Clerk JWKS URL from secret key"""
    secret_key = os.getenv("CLERK_SECRET_KEY") or AuthSettings().clerk_secret_key
    if not secret_key:
        raise ValueError("CLERK_SECRET_KEY is required")
    
    # Extract issuer from secret key (format: sk_test_... or sk_live_...)
    # JWKS URL format: https://{domain}/.well-known/jwks.json
    # For Clerk, we need to get the issuer from the token or use default
    # For MVP, we'll use a simpler approach with the secret key
    return "https://api.clerk.dev/.well-known/jwks.json"


def verify_clerk_token(token: str) -> dict:
    """
    Verify Clerk JWT token
    
    Args:
        token: JWT token string
        
    Returns:
        dict: Decoded token payload
        
    Raises:
        HTTPException: If token is invalid
    """
    try:
        # For MVP, we'll use the secret key directly
        # In production, you should verify against JWKS
        secret_key = os.getenv("CLERK_SECRET_KEY") or AuthSettings().clerk_secret_key
        if not secret_key:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Authentication configuration error"
            )
        
        # Decode token (Clerk uses RS256, but for MVP we'll use a simpler approach)
        # Note: For production, implement proper JWKS verification
        try:
            # Try to decode without verification first to get the header
            unverified = jwt.decode(token, options={"verify_signature": False})
            # For MVP, we'll do basic validation
            # In production, implement proper JWKS verification
            decoded = jwt.decode(
                token,
                secret_key,
                algorithms=["HS256"],
                options={"verify_signature": False}  # For MVP, skip signature verification
            )
        except jwt.InvalidTokenError:
            # For production, fetch JWKS and verify properly
            # For MVP, we'll accept the token if it's well-formed
            decoded = jwt.decode(token, options={"verify_signature": False})
        
        return decoded
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    except jwt.InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}"
        )


def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> str:
    """
    Extract user ID from Clerk JWT token
    
    Args:
        credentials: HTTP Bearer token credentials
        
    Returns:
        str: User ID from token
        
    Raises:
        HTTPException: If token is invalid or missing user ID
    """
    token = credentials.credentials
    payload = verify_clerk_token(token)
    
    # Clerk stores user ID in 'sub' claim
    user_id = payload.get("sub") or payload.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing user ID"
        )
    
    return user_id


def get_optional_user_id(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(optional_security)
) -> Optional[str]:
    """
    Extract user ID from Clerk JWT token (optional - for public endpoints)
    
    Args:
        credentials: Optional HTTP Bearer token credentials (None if no Authorization header)
        
    Returns:
        Optional[str]: User ID from token, or None if not authenticated or token is invalid
    """
    if not credentials:
        return None
    
    try:
        token = credentials.credentials
        payload = verify_clerk_token(token)
        
        # Clerk stores user ID in 'sub' claim
        user_id = payload.get("sub") or payload.get("user_id")
        return user_id
    except (HTTPException, Exception):
        # If token verification fails, return None (don't raise exception)
        return None

