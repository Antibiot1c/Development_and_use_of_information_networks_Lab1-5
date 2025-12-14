from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc
from ..db import get_db
from ..models import Post, Comment, User
from ..schemas import CommentCreate, CommentPublic
from ..deps import get_current_user

router = APIRouter(prefix="/api/comments", tags=["comments"])

@router.get("/post/{post_id}", response_model=list[CommentPublic])
def list_comments(post_id: int, db: Session = Depends(get_db), me: User = Depends(get_current_user)):
    if not db.query(Post).filter(Post.id == post_id).first():
        raise HTTPException(status_code=404, detail="Post not found")
    comments = db.query(Comment).filter(Comment.post_id == post_id).order_by(desc(Comment.created_at)).all()
    for c in comments:
        _ = c.author
    return comments

@router.post("/post/{post_id}", response_model=CommentPublic, status_code=201)
def add_comment(post_id: int, payload: CommentCreate, db: Session = Depends(get_db), me: User = Depends(get_current_user)):
    if not db.query(Post).filter(Post.id == post_id).first():
        raise HTTPException(status_code=404, detail="Post not found")
    c = Comment(post_id=post_id, author_id=me.id, text=payload.text)
    db.add(c)
    db.commit()
    db.refresh(c)
    c.author = me
    return c

@router.delete("/{comment_id}", status_code=204)
def delete_comment(comment_id: int, db: Session = Depends(get_db), me: User = Depends(get_current_user)):
    c = db.query(Comment).filter(Comment.id == comment_id).first()
    if not c:
        return
    if c.author_id != me.id and not me.is_admin:
        raise HTTPException(status_code=403, detail="Not allowed")
    db.delete(c)
    db.commit()
    return
