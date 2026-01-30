from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, APIKeyHeader
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

from strict.config import settings

# Configuration
SECRET_KEY = settings.auth_secret_key.get_secret_value()
ALGORITHM = settings.auth_algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = settings.auth_access_token_expire_minutes

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
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


async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    return token_data


async def verify_api_key(api_key: str = Depends(api_key_header)):
    """Verify API Key."""
    # In a real app, check against DB or secret setting
    # For now, simple check against a hardcoded value or env
    if not api_key:
        return None  # Proceed to check other auth methods or fail

    # Example: Check if it matches secret_key (not recommended for prod but ok for prototype)
    # Better: Use a separate valid_api_keys list in config
    if api_key == settings.secret_key.get_secret_value():
        return TokenData(username="api_key_user")

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid API Key",
    )


async def get_current_user_or_apikey(
    token_user: TokenData | None = Depends(lambda: None),  # Placeholder for OAuth
    api_key_user: TokenData | None = Depends(verify_api_key),
):
    """Allow either OAuth2 or API Key."""
    if api_key_user:
        return api_key_user
    # If no API key, try OAuth (needs proper chaining, simpler to just rely on Depends logic in route)
    # This is a bit complex to combine cleanly in one dependency without creating custom class
    # For simplicity, we'll enforce OAuth on routes, or API Key on routes.
    pass
