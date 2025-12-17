import os
import jwt
import logging
from jwt import PyJWKClient
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)


class AuthSettings(BaseSettings):
    """Settings for authentication"""
    supabase_url: str
    supabase_jwt_secret: Optional[str] = None  # Optional: for direct JWT verification
    
    class Config:
        env_file = ".env"
        extra = "ignore"  # Ignore extra environment variables


security = HTTPBearer()
optional_security = HTTPBearer(auto_error=False)

# Cache for JWKS client
_jwks_client: Optional[PyJWKClient] = None


def get_jwks_client() -> Optional[PyJWKClient]:
    """Get or create JWKS client for Supabase"""
    global _jwks_client
    if _jwks_client is None:
        settings = AuthSettings()
        # Supabase JWKS endpoint is at /auth/v1/.well-known/jwks.json
        jwks_url = f"{settings.supabase_url}/auth/v1/.well-known/jwks.json"
        try:
            _jwks_client = PyJWKClient(jwks_url)
            # Test the connection by trying to get the JWKS
            _jwks_client.get_signing_keys()
            logger.debug(f"JWKS client initialized: {jwks_url}")
        except Exception as e:
            logger.error(f"Failed to initialize JWKS client: {str(e)}")
            _jwks_client = None
    
    return _jwks_client


def verify_supabase_token(token: str) -> dict:
    """
    Verify Supabase JWT token using JWKS or JWT secret
    
    Args:
        token: JWT token string from Supabase
        
    Returns:
        dict: Decoded token payload
        
    Raises:
        HTTPException: If token is invalid
    """
    settings = AuthSettings()
    
    # First, decode token header to check algorithm
    try:
        unverified_header = jwt.get_unverified_header(token)
        algorithm = unverified_header.get("alg", "RS256")
    except Exception as e:
        logger.warning(f"Failed to decode token header: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token format: {str(e)}"
        )
    
    try:
        # Try JWKS verification (for RS256/ES256 tokens - ECDSA with P-256 curve)
        if algorithm in ["RS256", "ES256"]:
            jwks_client = get_jwks_client()
            if not jwks_client:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="JWKS client not initialized. Please check SUPABASE_URL configuration."
                )
            
            try:
                signing_key = jwks_client.get_signing_key_from_jwt(token)
                decoded = jwt.decode(
                    token,
                    signing_key.key,
                    algorithms=[algorithm],
                    issuer=f"{settings.supabase_url}/auth/v1",
                    options={"verify_aud": False}
                )
            except jwt.InvalidIssuerError as issuer_err:
                # If issuer verification fails, try without issuer verification
                logger.warning(f"Issuer verification failed, trying without issuer check: {str(issuer_err)}")
                signing_key = jwks_client.get_signing_key_from_jwt(token)
                decoded = jwt.decode(
                    token,
                    signing_key.key,
                    algorithms=[algorithm],
                    options={"verify_aud": False, "verify_iss": False}
                )
            
            # Log token verification success with user info
            user_id = decoded.get("sub")
            email = decoded.get("email")
            logger.info(f"Token verified via JWKS - User ID: {user_id}, Email: {email if email else 'N/A'}")
            
            return decoded
        elif algorithm == "HS256":
            # For HS256 tokens, check if they have a kid (key ID) - if so, use JWKS
            # Supabase may use key rotation even for HS256 tokens
            unverified_header = jwt.get_unverified_header(token)
            kid = unverified_header.get("kid")
            
            if kid:
                # Token has a kid, try JWKS first (Supabase key rotation)
                jwks_client = get_jwks_client()
                if jwks_client:
                    try:
                        signing_key = jwks_client.get_signing_key_from_jwt(token)
                        decoded = jwt.decode(
                            token,
                            signing_key.key,
                            algorithms=[algorithm],
                            issuer=f"{settings.supabase_url}/auth/v1",
                            options={"verify_aud": False}
                        )
                    except jwt.InvalidIssuerError:
                        signing_key = jwks_client.get_signing_key_from_jwt(token)
                        decoded = jwt.decode(
                            token,
                            signing_key.key,
                            algorithms=[algorithm],
                            options={"verify_aud": False, "verify_iss": False}
                        )
                    except Exception:
                        # Fall through to JWT secret verification
                        pass
                    else:
                        # JWKS verification succeeded
                        user_id = decoded.get("sub")
                        email = decoded.get("email")
                        return decoded
            
            # Fallback to JWT secret if no kid or JWKS failed
            if not settings.supabase_jwt_secret:
                logger.error("HS256 token detected but SUPABASE_JWT_SECRET is not configured")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="HS256 token detected but SUPABASE_JWT_SECRET is not configured. Please set SUPABASE_JWT_SECRET in your environment variables."
                )
            
            # For HS256, try with issuer verification first, fallback to no issuer verification
            try:
                decoded = jwt.decode(
                    token,
                    settings.supabase_jwt_secret,
                    algorithms=[algorithm],
                    issuer=f"{settings.supabase_url}/auth/v1",
                    options={"verify_aud": False}
                )
            except jwt.InvalidIssuerError:
                decoded = jwt.decode(
                    token,
                    settings.supabase_jwt_secret,
                    algorithms=[algorithm],
                    options={"verify_aud": False, "verify_iss": False}
                )
            except jwt.InvalidSignatureError as sig_err:
                logger.error(f"JWT signature verification failed: {str(sig_err)}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token signature verification failed. The SUPABASE_JWT_SECRET may not match your Supabase project's current JWT secret, or the token may be signed with a rotated key. Please check your Supabase project settings."
                )
            
            user_id = decoded.get("sub")
            email = decoded.get("email")
            
            return decoded
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Unsupported token algorithm: {algorithm}. Supabase tokens typically use ES256/RS256 (requires JWKS) or HS256 (requires SUPABASE_JWT_SECRET)."
            )
    except jwt.ExpiredSignatureError:
        logger.warning("Token verification failed: Token has expired")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    except jwt.InvalidTokenError as e:
        logger.warning(f"Token verification failed: Invalid token - {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Token verification failed with unexpected error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token verification failed: {str(e)}"
        )


def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> str:
    """
    Extract user ID from Supabase JWT token
    
    Args:
        credentials: HTTP Bearer token credentials
        
    Returns:
        str: User ID from token (sub claim)
        
    Raises:
        HTTPException: If token is invalid or missing user ID
    """
    token = credentials.credentials
    payload = verify_supabase_token(token)
    
    # Supabase stores user ID in 'sub' claim
    user_id = payload.get("sub")
    if not user_id:
        logger.warning("Token verified but missing user ID (sub claim)")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing user ID"
        )
    
    return user_id


def get_optional_user_id(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(optional_security)
) -> Optional[str]:
    """
    Extract user ID from Supabase JWT token (optional - for public endpoints)
    
    Args:
        credentials: Optional HTTP Bearer token credentials (None if no Authorization header)
        
    Returns:
        Optional[str]: User ID from token, or None if not authenticated or token is invalid
    """
    if not credentials:
        return None
    
    try:
        token = credentials.credentials
        payload = verify_supabase_token(token)
        
        # Supabase stores user ID in 'sub' claim
        user_id = payload.get("sub")
        return user_id
    except (HTTPException, Exception):
        # If token verification fails, return None (don't raise exception)
        return None

