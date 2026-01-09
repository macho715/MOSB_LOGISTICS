import os
from datetime import datetime, timedelta, timezone
from typing import Optional, Literal

from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel


Role = Literal["OPS", "FINANCE", "COMPLIANCE", "ADMIN"]

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-prod")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


class User(BaseModel):
    username: str
    email: str
    role: Role
    disabled: bool = False


class UserInDB(User):
    hashed_password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None
    role: Optional[Role] = None


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


# Temporary in-memory users (replace with DB in production).
fake_users_db = {
    "ops_user": {
        "username": "ops_user",
        "email": "ops@example.com",
        "role": "OPS",
        "hashed_password": get_password_hash("ops123"),
        "disabled": False,
    },
    "finance_user": {
        "username": "finance_user",
        "email": "finance@example.com",
        "role": "FINANCE",
        "hashed_password": get_password_hash("finance123"),
        "disabled": False,
    },
    "compliance_user": {
        "username": "compliance_user",
        "email": "compliance@example.com",
        "role": "COMPLIANCE",
        "hashed_password": get_password_hash("compliance123"),
        "disabled": False,
    },
    "admin": {
        "username": "admin",
        "email": "admin@example.com",
        "role": "ADMIN",
        "hashed_password": get_password_hash("admin123"),
        "disabled": False,
    },
}


def get_user(username: str) -> Optional[UserInDB]:
    user_dict = fake_users_db.get(username)
    if not user_dict:
        return None
    return UserInDB(**user_dict)


def authenticate_user(username: str, password: str) -> Optional[User]:
    user = get_user(username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    if user.disabled:
        return None
    return User(**user.model_dump(exclude={"hashed_password"}))


async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: Optional[str] = payload.get("sub")
        role: Optional[str] = payload.get("role")
        if not username:
            raise credentials_exception
        token_data = TokenData(username=username, role=role)  # type: ignore[arg-type]
    except Exception:
        raise credentials_exception

    user = get_user(token_data.username or "")
    if not user:
        raise credentials_exception
    if user.disabled:
        raise credentials_exception
    return User(**user.model_dump(exclude={"hashed_password"}))
