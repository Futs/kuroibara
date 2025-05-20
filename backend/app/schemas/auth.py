from typing import Optional
from pydantic import BaseModel, Field


class Token(BaseModel):
    """Token schema."""
    
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    """Token payload schema."""
    
    sub: str
    exp: int
    type: str


class Login(BaseModel):
    """Login schema."""
    
    username: str
    password: str
    totp_code: Optional[str] = None


class RefreshToken(BaseModel):
    """Refresh token schema."""
    
    refresh_token: str


class TwoFactorSetup(BaseModel):
    """Two-factor setup schema."""
    
    secret: str
    qr_code: str


class TwoFactorVerify(BaseModel):
    """Two-factor verification schema."""
    
    code: str = Field(..., min_length=6, max_length=6)
