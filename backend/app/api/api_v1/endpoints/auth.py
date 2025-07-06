from datetime import timedelta
from typing import Any
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from jose import jwt, JWTError
from redis.asyncio import Redis

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    verify_password,
    get_password_hash,
    generate_totp_secret,
    get_totp_uri,
    verify_totp,
    generate_qr_code,
)
from app.core.deps import get_current_user, get_db, oauth2_scheme, redis_client
from app.models.user import User
from app.schemas.auth import (
    Token,
    Login,
    LoginResponse,
    RefreshToken,
    TwoFactorSetup,
    TwoFactorVerify,
    TokenPayload,
)
from app.schemas.user import UserCreate, User as UserSchema

router = APIRouter()


@router.post("/login", response_model=LoginResponse)
async def login(
    login_data: Login,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Login for access token.
    """
    # Find user by username or email
    result = await db.execute(
        select(User).where(
            (User.username == login_data.username) | (User.email == login_data.username)
        )
    )
    user = result.scalars().first()

    # Check if user exists and password is correct
    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )

    # Check 2FA if enabled
    if user.two_fa_enabled:
        if not login_data.totp_code:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="2FA code required",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not verify_totp(user.two_fa_secret, login_data.totp_code):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid 2FA code",
                headers={"WWW-Authenticate": "Bearer"},
            )

    # Create access and refresh tokens
    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": UserSchema.model_validate(user),
    }


@router.post("/refresh", response_model=Token)
async def refresh_token(
    refresh_token_data: RefreshToken,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Refresh access token.
    """
    try:
        # Decode refresh token
        payload = jwt.decode(
            refresh_token_data.refresh_token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        token_data = TokenPayload(**payload)

        # Check if token is a refresh token
        if token_data.type != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Get user ID from token
        user_id = token_data.sub
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Get user from database
        user = await db.get(User, uuid.UUID(user_id))
        if user is None or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Create new access and refresh tokens
        access_token = create_access_token(user.id)
        refresh_token = create_refresh_token(user.id)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        }
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.post("/register", response_model=UserSchema)
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Register a new user.
    """
    try:
        # Check if username already exists
        result = await db.execute(select(User).where(User.username == user_data.username))
        if result.scalars().first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Registration failed: Username '{user_data.username}' is already taken. Please choose a different username.",
            )

        # Check if email already exists
        result = await db.execute(select(User).where(User.email == user_data.email))
        if result.scalars().first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Registration failed: Email '{user_data.email}' is already registered. Please use a different email address or try logging in.",
            )

        # Create new user
        user = User(
            username=user_data.username,
            email=user_data.email,
            hashed_password=get_password_hash(user_data.password),
            full_name=user_data.full_name,
        )

        db.add(user)
        await db.commit()
        await db.refresh(user)

        return user

    except HTTPException:
        # Re-raise HTTP exceptions (validation errors)
        raise
    except Exception as e:
        # Handle any other database or system errors
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: An unexpected error occurred while creating your account. Please try again later. Error: {str(e)}",
        )


@router.post("/2fa/setup", response_model=TwoFactorSetup)
async def setup_2fa(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Setup 2FA for the current user.
    """
    # Generate TOTP secret
    secret = generate_totp_secret()

    # Generate QR code
    uri = get_totp_uri(secret, current_user.username)
    qr_code = generate_qr_code(uri)

    # Update user with new secret (not enabled yet)
    current_user.two_fa_secret = secret
    await db.commit()

    return {
        "secret": secret,
        "qr_code": qr_code,
    }


@router.post("/2fa/verify", response_model=UserSchema)
async def verify_2fa_setup(
    verification_data: TwoFactorVerify,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Verify and enable 2FA for the current user.
    """
    # Check if user has a TOTP secret
    if not current_user.two_fa_secret:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="2FA not set up",
        )

    # Verify TOTP code
    if not verify_totp(current_user.two_fa_secret, verification_data.code):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification code",
        )

    # Enable 2FA
    current_user.two_fa_enabled = True
    await db.commit()
    await db.refresh(current_user)

    return current_user


@router.post("/2fa/disable", response_model=UserSchema)
async def disable_2fa(
    verification_data: TwoFactorVerify,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Disable 2FA for the current user.
    """
    # Check if 2FA is enabled
    if not current_user.two_fa_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="2FA not enabled",
        )

    # Verify TOTP code
    if not verify_totp(current_user.two_fa_secret, verification_data.code):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification code",
        )

    # Disable 2FA
    current_user.two_fa_enabled = False
    current_user.two_fa_secret = None
    await db.commit()
    await db.refresh(current_user)

    return current_user


@router.post("/logout")
async def logout(
    token: str = Depends(oauth2_scheme),
) -> Any:
    """
    Logout user by blacklisting the current token.
    """
    try:
        # Decode token to get expiration time
        payload = jwt.decode(
            token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
        token_data = TokenPayload(**payload)

        # Calculate TTL for blacklist (time until token expires)
        import time
        current_time = int(time.time())
        ttl = token_data.exp - current_time

        # Only blacklist if token hasn't expired yet and Redis is available
        if ttl > 0 and redis_client:
            try:
                # Add token to blacklist with TTL
                await redis_client.setex(f"blacklist:{token}", ttl, "1")
            except Exception:
                # If Redis operation fails, continue anyway
                pass

    except JWTError:
        # If token is invalid, just return success anyway
        pass

    return {"message": "Successfully logged out"}