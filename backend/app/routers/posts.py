import os
import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from ..db import get_db
from ..models import Post, User, Like, Comment, Follow
from ..schemas import PostPublic
from ..deps import get_current_user
from ..config import settings

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "static", "uploads")

router = APIRouter(prefix="/api/posts", tags=["posts"])

def _post_to_public(db: Session, post: Post, me_id: int | None) -> PostPublic:
    image_url = f"/static/uploads/{post.image_path}" if post.image_path else None
    likes_count = db.query(func.count(Like.post_id)).filter(Like.post_id == post.id).scalar() or 0
    comments_count = db.query(func.count(Comment.post_id)).filter(Comment.post_id == post.id).scalar() or 0
    liked_by_me = False
    if me_id:
        liked_by_me = db.query(Like).filter(Like.post_id == post.id, Like.user_id == me_id).first() is not None
    return PostPublic(
        id=post.id,
        caption=post.caption,
        image_url=image_url,
        created_at=post.created_at,
        author=post.author,
        likes_count=likes_count,
        comments_count=comments_count,
        liked_by_me=liked_by_me,
    )

@router.post("", response_model=PostPublic, status_code=201)
def create_post(
    caption: str = Form(default=""),
    image: UploadFile | None = File(default=None),
    db: Session = Depends(get_db),
    me: User = Depends(get_current_user),
):
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    filename = None
    if image:
        if image.content_type not in {"image/png", "image/jpeg", "image/webp"}:
            raise HTTPException(status_code=400, detail="Only PNG/JPEG/WEBP images allowed")
        ext = {"image/png": ".png", "image/jpeg": ".jpg", "image/webp": ".webp"}[image.content_type]
        filename = f"{uuid.uuid4().hex}{ext}"
        out_path = os.path.join(UPLOAD_DIR, filename)
        with open(out_path, "wb") as f:
            f.write(image.file.read())

    post = Post(author_id=me.id, caption=caption, image_path=filename)
    db.add(post)
    db.commit()
    db.refresh(post)
    post.author = me
    return _post_to_public(db, post, me.id)

@router.get("/{post_id}", response_model=PostPublic)
def get_post(post_id: int, db: Session = Depends(get_db), me: User = Depends(get_current_user)):
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return _post_to_public(db, post, me.id)

@router.delete("/{post_id}", status_code=204)
def delete_post(post_id: int, db: Session = Depends(get_db), me: User = Depends(get_current_user)):
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        return
    if post.author_id != me.id and not me.is_admin:
        raise HTTPException(status_code=403, detail="Not allowed")
    if post.image_path:
        try:
            os.remove(os.path.join(UPLOAD_DIR, post.image_path))
        except FileNotFoundError:
            pass
    db.delete(post)
    db.commit()
    return

@router.get("", response_model=list[PostPublic])
def list_my_posts(db: Session = Depends(get_db), me: User = Depends(get_current_user)):
    posts = db.query(Post).filter(Post.author_id == me.id).order_by(desc(Post.created_at)).all()
    for p in posts:
        _ = p.author
    return [_post_to_public(db, p, me.id) for p in posts]

@router.get("/feed/me", response_model=list[PostPublic])
def feed(db: Session = Depends(get_db), me: User = Depends(get_current_user), limit: int = 30):
    following_ids = [x[0] for x in db.query(Follow.following_id).filter(Follow.follower_id == me.id).all()]
    ids = set(following_ids + [me.id])
    q = db.query(Post).filter(Post.author_id.in_(ids)).order_by(desc(Post.created_at)).limit(limit)
    posts = q.all()
    if not posts:
        posts = db.query(Post).order_by(desc(Post.created_at)).limit(limit).all()
    for p in posts:
        _ = p.author
    return [_post_to_public(db, p, me.id) for p in posts]
