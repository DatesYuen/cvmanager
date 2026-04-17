from typing import Optional, Dict
from datetime import datetime
from pydantic import BaseModel, Field


class UserBase(BaseModel):
    username: str
    display_name: str = ""
    role: str = "user"
    permissions: Dict[str, bool] = Field(default_factory=dict)
    is_active: bool = True


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    display_name: Optional[str] = None
    role: Optional[str] = None
    permissions: Optional[Dict[str, bool]] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None


class UserOut(UserBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut
