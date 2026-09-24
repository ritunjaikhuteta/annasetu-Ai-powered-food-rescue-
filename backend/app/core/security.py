"""Security and Token Verification Utilities."""

import logging
from typing import Any, Dict, Optional
import jwt
from app.core.config import settings
from app.db.supabase import SupabaseClient, get_supabase_client
from app.schemas.auth import AuthenticatedUser
from app.utils.exceptions import UnauthorizedException

logger = logging.getLogger("annasetu.security")


async def verify_supabase_token(
    token: str,
    db_client: Optional[SupabaseClient] = None,
) -> AuthenticatedUser:
    """Verify Supabase JWT token either via JWT secret signature or Supabase Auth API.

    Returns:
        AuthenticatedUser schema containing user ID, email, and metadata.
    Raises:
        UnauthorizedException on invalid, expired, or rejected token.
    """
    if not token or not token.strip():
        raise UnauthorizedException("Authorization token is missing.")

    # 1. If SUPABASE_JWT_SECRET is configured, attempt secure signature verification
    if settings.SUPABASE_JWT_SECRET:
        try:
            payload = jwt.decode(
                token,
                settings.SUPABASE_JWT_SECRET,
                algorithms=["HS256"],
                options={"verify_aud": False},  # Supabase aud defaults to 'authenticated'
            )
            user_id = payload.get("sub")
            if not user_id:
                raise UnauthorizedException("Invalid token payload: missing subject claim.")

            return AuthenticatedUser(
                id=user_id,
                email=payload.get("email"),
                phone=payload.get("phone"),
                app_metadata=payload.get("app_metadata", {}),
                user_metadata=payload.get("user_metadata", {}),
            )
        except jwt.ExpiredSignatureError:
            raise UnauthorizedException("Your session has expired. Please sign in again.")
        except jwt.PyJWTError as e:
            logger.warning("Local JWT validation failed: %s. Falling back to Supabase auth API.", e)

    # 2. Server-side Supabase Auth API verification
    client = db_client or get_supabase_client()
    user_data = await client.verify_user_jwt(token)
    if not user_data or "id" not in user_data:
        raise UnauthorizedException("Invalid or expired session. Please sign in again.")

    return AuthenticatedUser(
        id=user_data["id"],
        email=user_data.get("email"),
        phone=user_data.get("phone"),
        app_metadata=user_data.get("app_metadata", {}),
        user_metadata=user_data.get("user_metadata", {}),
    )
