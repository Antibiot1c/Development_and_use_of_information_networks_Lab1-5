from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..db import get_db
from ..models import Post, Like, User
from ..deps import get_current_user

router = APIRouter(prefix="/api/likes", tags=["likes"])

@router.post("/post/{post_id}", status_code=204)
def like(post_id: int, db: Session = Depends(get_db), me: User = Depends(get_current_user)):
    if not db.query(Post).filter(Post.id == post_id).first():
        raise HTTPException(status_code=404, detail="Post not found")
    exists = db.query(Like).filter(Like.post_id == post_id, Like.user_id == me.id).first()
    if not exists:
        db.add(Like(post_id=post_id, user_id=me.id))
        db.commit()
    return

@router.post("/post/{post_id}/unlike", status_code=204)
def unlike(post_id: int, db: Session = Depends(get_db), me: User = Depends(get_current_user)):
    db.query(Like).filter(Like.post_id == post_id, Like.user_id == me.id).delete()
    db.commit()
    return
