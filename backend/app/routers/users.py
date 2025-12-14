from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..db import get_db
from ..models import User, Post, Follow
from ..schemas import UserPublic
from ..deps import get_current_user

router = APIRouter(prefix="/api/users", tags=["users"])

@router.get("/{username}", response_model=UserPublic)
def get_user(username: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.post("/{username}/follow", status_code=204)
def follow(username: str, db: Session = Depends(get_db), me: User = Depends(get_current_user)):
    target = db.query(User).filter(User.username == username).first()
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    if target.id == me.id:
        raise HTTPException(status_code=400, detail="Cannot follow yourself")
    exists = db.query(Follow).filter(Follow.follower_id == me.id, Follow.following_id == target.id).first()
    if not exists:
        db.add(Follow(follower_id=me.id, following_id=target.id))
        db.commit()
    return

@router.post("/{username}/unfollow", status_code=204)
def unfollow(username: str, db: Session = Depends(get_db), me: User = Depends(get_current_user)):
    target = db.query(User).filter(User.username == username).first()
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    db.query(Follow).filter(Follow.follower_id == me.id, Follow.following_id == target.id).delete()
    db.commit()
    return
