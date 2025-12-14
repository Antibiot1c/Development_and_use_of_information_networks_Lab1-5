from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from .db import engine
from .models import Base
from .routers import auth, users, posts, comments, likes, admin, pages

def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.frontend_origin],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    Base.metadata.create_all(bind=engine)

    app.mount("/static", StaticFiles(directory="app/static"), name="static")

    app.include_router(auth.router)
    app.include_router(users.router)
    app.include_router(posts.router)
    app.include_router(comments.router)
    app.include_router(likes.router)
    app.include_router(admin.router)
    app.include_router(pages.router)

    return app

app = create_app()
