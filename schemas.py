from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field


class ItemBase(BaseModel):
    name: str
    price: float


class ItemCreate(ItemBase):
    pass


class ItemResponse(ItemBase):
    id: int
    created_at: datetime
    updated_at: datetime
    created_by: str
    updated_by: str | None = None

    class Config:
        from_attributes = True


class PaginatedItems(BaseModel):
    total: int
    skip: int
    limit: int
    items: list[ItemResponse]


class UserBase(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: EmailStr


class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=128)


class UserResponse(UserBase):
    id: int
    is_active: bool
    role: str
    created_at: datetime

    class Config:
        from_attributes = True


class PaginatedUsers(BaseModel):
    total: int
    skip: int
    limit: int
    users: list[UserResponse]


class UserRoleUpdate(BaseModel):
    role: Literal["user", "admin"]


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    username: str | None = None
