from typing import Generator, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis
import uuid
from datetime import datetime, timezone

from app.core.config import settings
from app.core.security import verify_totp
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import TokenPayload

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


# Global Redis instance (will be set during startup)
redis_client: Optional[Redis] = None


# Dependency to get Redis connection
async def get_redis() -> Redis:
    """Get Redis connection."""
    if redis_client is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Redis connection not available"
        )
    return redis_client


# Function to set Redis client (called during startup)
def set_redis_client(client: Redis) -> None:
    """Set the global Redis client."""
    global redis_client
    redis_client = client


# Dependency to get current user
async def get_current_user(
    db: AsyncSession = Depends(get_db),
    token: str = Depends(oauth2_scheme),
) -> User:
    """Get the current authenticated user."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # Check if token is blacklisted (only if Redis is available)
        if redis_client:
            try:
                is_blacklisted = await redis_client.get(f"blacklist:{token}")
                if is_blacklisted:
                    raise credentials_exception
            except Exception:
                # If Redis check fails, continue without blacklist check
                pass

        # Decode JWT token
        payload = jwt.decode(
            token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
        token_data = TokenPayload(**payload)

        # Check if token is an access token
        if token_data.type != "access":
            raise credentials_exception

        # Check if token is expired
        if token_data.exp < int(datetime.now(timezone.utc).timestamp()):
            raise credentials_exception

        # Get user ID from token
        user_id = token_data.sub
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    # Get user from database
    user = await db.get(User, uuid.UUID(user_id))
    if user is None:
        raise credentials_exception

    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )

    return user


# Dependency to get current active superuser
async def get_current_active_superuser(
    current_user: User = Depends(get_current_user),
) -> User:
    """Get the current authenticated superuser."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )

    return current_user


# Dependency to verify 2FA if enabled
async def verify_2fa(
    current_user: User = Depends(get_current_user),
    totp_code: Optional[str] = None,
) -> User:
    """Verify 2FA if enabled."""
    if current_user.two_fa_enabled:
        if not totp_code:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="2FA code required",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not verify_totp(current_user.two_fa_secret, totp_code):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid 2FA code",
                headers={"WWW-Authenticate": "Bearer"},
            )

    return current_user
