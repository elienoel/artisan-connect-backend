import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.user import User, UserRole

# HTTPBearer (rather than OAuth2PasswordBearer) matches how /auth/login actually
# works here: a JSON body, not an OAuth2 form post. It also gives Swagger UI's
# "Authorize" dialog a plain "paste your token" field instead of a login form
# that would post to a URL this API doesn't implement.
bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if credentials is None:
        raise credentials_exception

    user_id = decode_access_token(credentials.credentials)
    if user_id is None:
        raise credentials_exception

    user = db.get(User, uuid.UUID(user_id))
    if user is None or not user.is_active:
        raise credentials_exception
    return user


def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User | None:
    """Like get_current_user, but returns None instead of raising when there's
    no (or an invalid) token — for endpoints usable both anonymously and
    authenticated, where auth only changes the response (e.g. excluding the
    caller's own listing from search results)."""
    if credentials is None:
        return None
    user_id = decode_access_token(credentials.credentials)
    if user_id is None:
        return None
    user = db.get(User, uuid.UUID(user_id))
    if user is None or not user.is_active:
        return None
    return user


def get_current_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return current_user


def get_current_user_ws(token: str, db: Session) -> User | None:
    user_id = decode_access_token(token)
    if user_id is None:
        return None
    user = db.get(User, uuid.UUID(user_id))
    if user is None or not user.is_active:
        return None
    return user
