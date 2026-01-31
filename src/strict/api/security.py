from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import (
    OAuth2PasswordBearer,
    APIKeyHeader,
)
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, SecretStr

from strict.config import settings

# Configuration
SECRET_KEY = settings.auth_secret_key.get_secret_value()
ALGORITHM = settings.auth_algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = settings.auth_access_token_expire_minutes

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password using bcrypt."""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
) -> Optional[TokenData]:
    """Get current user from OAuth2 token.

    Returns TokenData if token is valid, None otherwise.
    """
    if token is None:
        return None

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: Optional[str] = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError as e:
        raise credentials_exception from e
    return token_data


async def verify_api_key(
    api_key: Optional[str] = Depends(api_key_header),
) -> Optional[TokenData]:
    """Verify API Key against configured valid keys.

    Returns TokenData if API key is valid, None otherwise.
    """
    if not api_key:
        return None

    # Check against configured valid API keys
    valid_keys = [key.get_secret_value() for key in settings.valid_api_keys]
    if api_key in valid_keys:
        return TokenData(username="api_key_user")

    # Don't raise here - just return None to allow other auth methods
    return None


async def get_current_user_or_apikey(
    token_user: Optional[TokenData] = Depends(get_current_user),
    api_key_user: Optional[TokenData] = Depends(verify_api_key),
) -> TokenData:
    """Allow either OAuth2 or API Key authentication."""
    if api_key_user:
        return api_key_user
    if token_user:
        return token_user
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
    )
