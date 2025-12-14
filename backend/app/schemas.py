from pydantic import BaseModel, EmailStr, Field
from datetime import datetime

class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=32, pattern=r"^[a-zA-Z0-9_]+$")
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

class UserPublic(BaseModel):
    id: int
    username: str
    email: EmailStr
    is_admin: bool
    created_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class PostCreate(BaseModel):
    caption: str = Field(default="", max_length=1000)

class PostPublic(BaseModel):
    id: int
    caption: str
    image_url: str | None
    created_at: datetime
    author: UserPublic
    likes_count: int
    comments_count: int
    liked_by_me: bool = False

class CommentCreate(BaseModel):
    text: str = Field(min_length=1, max_length=1000)

class CommentPublic(BaseModel):
    id: int
    text: str
    created_at: datetime
    author: UserPublic

class FeedResponse(BaseModel):
    items: list[PostPublic]
