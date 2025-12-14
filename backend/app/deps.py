from fastapi import Depends, Cookie, HTTPException, status, Header
from sqlalchemy.orm import Session
from .db import get_db
from .auth import decode_access_token
from .models import User

def _get_token_from_cookie(access_token: str | None) -> str | None:
    if not access_token:
        return None
    # allow either raw JWT or "Bearer <jwt>"
    parts = access_token.split(" ", 1)
    return parts[1] if len(parts) == 2 and parts[0].lower() == "bearer" else access_token

def get_current_user(
    db: Session = Depends(get_db),
    authorization: str | None = Header(default=None),
    access_token: str | None = Cookie(default=None),
):
    token = None
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1]
    if not token:
        token = _get_token_from_cookie(access_token)
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    user_id = int(decode_access_token(token))
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user

def require_admin(user: User = Depends(get_current_user)):
    if not user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin only")
    return user
