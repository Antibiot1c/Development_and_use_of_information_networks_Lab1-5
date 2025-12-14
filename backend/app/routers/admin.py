from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import desc
from ..db import get_db
from ..deps import require_admin
from ..models import User, Post

router = APIRouter(prefix="/api/admin", tags=["admin"])

@router.get("/users")
def list_users(db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    users = db.query(User).order_by(desc(User.created_at)).all()
    return [{"id": u.id, "username": u.username, "email": u.email, "is_admin": u.is_admin, "created_at": u.created_at} for u in users]

@router.get("/posts")
def list_posts(db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    posts = db.query(Post).order_by(desc(Post.created_at)).all()
    return [{"id": p.id, "author_id": p.author_id, "caption": p.caption, "image_path": p.image_path, "created_at": p.created_at} for p in posts]
