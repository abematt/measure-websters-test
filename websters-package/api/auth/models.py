from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class User(BaseModel):
    """User model for MongoDB storage"""
    username: str = Field(..., min_length=3, max_length=50)
    email: Optional[str] = None
    hashed_password: str
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None

class UserInDB(User):
    """User model with MongoDB _id"""
    id: Optional[str] = Field(None, alias="_id")

class LoginRequest(BaseModel):
    """Login request model"""
    username: str = Field(...)
    password: str = Field(...)

class LoginResponse(BaseModel):
    """Login response model"""
    access_token: str
    token_type: str = "bearer"
    user: dict

class TokenData(BaseModel):
    """Token payload model"""
    username: Optional[str] = None