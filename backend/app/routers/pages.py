from __future__ import annotations

from fastapi import APIRouter, Depends, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import desc, func

from ..db import get_db
from ..models import Post, Like, Comment, Follow, User
from ..deps import get_current_user
from ..auth import hash_password, verify_password, create_access_token, decode_access_token

templates = Jinja2Templates(directory="app/templates")
router = APIRouter(tags=["pages"])


def avatar(username: str) -> str:
    # External service (Lab 2 requirement): DiceBear avatar generator
    return f"https://api.dicebear.com/8.x/thumbs/svg?seed={username}"


def _redirect(url: str) -> RedirectResponse:
    return RedirectResponse(url=url, status_code=303)


def _token_from_cookie(request: Request) -> str | None:
    raw = request.cookies.get("access_token")
    if not raw:
        return None
    parts = raw.split(" ", 1)
    if len(parts) == 2 and parts[0].lower() == "bearer":
        return parts[1]
    return raw


def get_me_optional(request: Request, db: Session) -> User | None:
    token = _token_from_cookie(request)
    if not token:
        return None
    try:
        user_id = int(decode_access_token(token))
    except Exception:
        return None
    return db.get(User, user_id)


@router.get("/", response_class=HTMLResponse)
def home(request: Request, db: Session = Depends(get_db)):
    posts = db.query(Post).order_by(desc(Post.created_at)).limit(20).all()
    for p in posts:
        _ = p.author
    me = get_me_optional(request, db)
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "posts": posts, "avatar": avatar, "me": me},
    )


@router.get("/about", response_class=HTMLResponse)
def about(request: Request, db: Session = Depends(get_db)):
    me = get_me_optional(request, db)
    return templates.TemplateResponse("about.html", {"request": request, "me": me})


@router.get("/app", response_class=HTMLResponse)
def app_feed(
    request: Request,
    db: Session = Depends(get_db),
    me: User = Depends(get_current_user),
):
    following_ids = [x[0] for x in db.query(Follow.following_id).filter(Follow.follower_id == me.id).all()]
    ids = set(following_ids + [me.id])

    posts = (
        db.query(Post)
        .filter(Post.author_id.in_(ids))
        .order_by(desc(Post.created_at))
        .limit(50)
        .all()
    )
    for p in posts:
        _ = p.author

    like_map = {
        pid: c
        for pid, c in db.query(Like.post_id, func.count(Like.post_id)).group_by(Like.post_id).all()
    }
    comment_map = {
        pid: c
        for pid, c in db.query(Comment.post_id, func.count(Comment.post_id)).group_by(Comment.post_id).all()
    }
    liked_set = set([x[0] for x in db.query(Like.post_id).filter(Like.user_id == me.id).all()])

    return templates.TemplateResponse(
        "feed.html",
        {
            "request": request,
            "me": me,
            "posts": posts,
            "avatar": avatar,
            "like_map": like_map,
            "comment_map": comment_map,
            "liked_set": liked_set,
        },
    )


@router.get("/profile/{username}", response_class=HTMLResponse)
def profile(
    username: str,
    request: Request,
    db: Session = Depends(get_db),
    me: User = Depends(get_current_user),
):
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return _redirect("/")

    posts = db.query(Post).filter(Post.author_id == user.id).order_by(desc(Post.created_at)).all()
    follows = (
        db.query(Follow)
        .filter(Follow.follower_id == me.id, Follow.following_id == user.id)
        .first()
        is not None
    )

    follower_count = db.query(func.count(Follow.follower_id)).filter(Follow.following_id == user.id).scalar() or 0
    following_count = db.query(func.count(Follow.following_id)).filter(Follow.follower_id == user.id).scalar() or 0

    return templates.TemplateResponse(
        "profile.html",
        {
            "request": request,
            "me": me,
            "user": user,
            "posts": posts,
            "avatar": avatar,
            "follows": follows,
            "follower_count": int(follower_count),
            "following_count": int(following_count),
        },
    )


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request, db: Session = Depends(get_db)):
    me = get_me_optional(request, db)
    if me:
        return _redirect("/app")
    return templates.TemplateResponse("login.html", {"request": request, "error": None})


@router.post("/login", response_class=HTMLResponse)
def login_submit(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    username = (username or "").strip()
    user = db.query(User).filter(User.username == username).first()

    if not user or not verify_password(password, user.hashed_password):
        return templates.TemplateResponse(
            "login.html", {"request": request, "error": "Invalid username or password."}, status_code=400
        )

    token = create_access_token(subject=str(user.id))
    resp = _redirect("/app")
    resp.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        samesite="lax",
        secure=False,
        max_age=60 * 60 * 24,
        path="/",
    )
    return resp


@router.get("/register", response_class=HTMLResponse)
def register_page(request: Request, db: Session = Depends(get_db)):
    me = get_me_optional(request, db)
    if me:
        return _redirect("/app")
    return templates.TemplateResponse("register.html", {"request": request, "error": None})


@router.post("/register", response_class=HTMLResponse)
def register_submit(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    username = (username or "").strip()
    email = (email or "").strip().lower()

    if len(username) < 3:
        return templates.TemplateResponse("register.html", {"request": request, "error": "Username too short."}, status_code=400)

    if "@" not in email or "." not in email:
        return templates.TemplateResponse("register.html", {"request": request, "error": "Invalid email."}, status_code=400)

    if len(password) < 6:
        return templates.TemplateResponse("register.html", {"request": request, "error": "Password too short."}, status_code=400)

    if db.query(User).filter(User.username == username).first():
        return templates.TemplateResponse("register.html", {"request": request, "error": "Username already exists."}, status_code=400)

    if db.query(User).filter(User.email == email).first():
        return templates.TemplateResponse("register.html", {"request": request, "error": "Email already exists."}, status_code=400)

    user = User(
        username=username,
        email=email,
        hashed_password=hash_password(password),
        is_admin=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(sub=str(user.id))
    resp = RedirectResponse(url="/app", status_code=303)
    resp.set_cookie("access_token", token, httponly=True, samesite="lax", secure=False, max_age=60 * 60 * 24, path="/")
    return resp



@router.post("/logout")
def logout():
    resp = _redirect("/")
    resp.delete_cookie("access_token", path="/")
    return resp


@router.post("/actions/post")
def create_post(
    caption: str = Form(default=""),
    image_url: str = Form(default=""),
    db: Session = Depends(get_db),
    me: User = Depends(get_current_user),
):
    caption = (caption or "").strip()
    image_url = (image_url or "").strip()

    if len(caption) > 2000:
        raise HTTPException(status_code=400, detail="Caption too long")

    p = Post(author_id=me.id, caption=caption, image_path=image_url or None)
    db.add(p)
    db.commit()
    return _redirect("/app")


@router.post("/actions/like/{post_id}")
def like_post(
    post_id: int,
    db: Session = Depends(get_db),
    me: User = Depends(get_current_user),
):
    post = db.get(Post, post_id)
    if not post:
        return _redirect("/app")

    existing = db.query(Like).filter(Like.user_id == me.id, Like.post_id == post_id).first()
    if not existing:
        db.add(Like(user_id=me.id, post_id=post_id))
        db.commit()
    return _redirect("/app")


@router.post("/actions/unlike/{post_id}")
def unlike_post(
    post_id: int,
    db: Session = Depends(get_db),
    me: User = Depends(get_current_user),
):
    db.query(Like).filter(Like.user_id == me.id, Like.post_id == post_id).delete()
    db.commit()
    return _redirect("/app")


@router.post("/actions/comment/{post_id}")
def add_comment(
    post_id: int,
    text: str = Form(default=""),
    db: Session = Depends(get_db),
    me: User = Depends(get_current_user),
):
    text = (text or "").strip()
    if not text:
        return _redirect("/app")
    if len(text) > 500:
        raise HTTPException(status_code=400, detail="Comment too long")
    post = db.get(Post, post_id)
    if not post:
        return _redirect("/app")
    db.add(Comment(author_id=me.id, post_id=post_id, text=text))
    db.commit()
    return _redirect("/app")


@router.post("/actions/follow/{username}")
def follow_user(
    username: str,
    db: Session = Depends(get_db),
    me: User = Depends(get_current_user),
):
    user = db.query(User).filter(User.username == username).first()
    if not user or user.id == me.id:
        return _redirect(f"/profile/{username}")

    existing = (
        db.query(Follow)
        .filter(Follow.follower_id == me.id, Follow.following_id == user.id)
        .first()
    )
    if not existing:
        db.add(Follow(follower_id=me.id, following_id=user.id))
        db.commit()
    return _redirect(f"/profile/{username}")


@router.post("/actions/unfollow/{username}")
def unfollow_user(
    username: str,
    db: Session = Depends(get_db),
    me: User = Depends(get_current_user),
):
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return _redirect("/app")

    db.query(Follow).filter(Follow.follower_id == me.id, Follow.following_id == user.id).delete()
    db.commit()
    return _redirect(f"/profile/{username}")
