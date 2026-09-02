import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login", auto_error=False)


def get_current_user(
    token: str | None = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if token is None:
        raise credentials_exception

    user_id = decode_access_token(token)
    if user_id is None:
        raise credentials_exception

    user = db.get(User, uuid.UUID(user_id))
    if user is None or not user.is_active:
        raise credentials_exception
    return user


def get_current_user_optional(
    token: str | None = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User | None:
    """Like get_current_user, but returns None instead of raising when there's
    no (or an invalid) token — for endpoints usable both anonymously and
    authenticated, where auth only changes the response (e.g. excluding the
    caller's own listing from search results)."""
    if token is None:
        return None
    user_id = decode_access_token(token)
    if user_id is None:
        return None
    user = db.get(User, uuid.UUID(user_id))
    if user is None or not user.is_active:
        return None
    return user


def get_current_user_ws(token: str, db: Session) -> User | None:
    user_id = decode_access_token(token)
    if user_id is None:
        return None
    user = db.get(User, uuid.UUID(user_id))
    if user is None or not user.is_active:
        return None
    return user
