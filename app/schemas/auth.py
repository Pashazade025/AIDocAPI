from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional


class UserRegister(BaseModel):
    """Schema for user registration"""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6, max_length=100)


class UserLogin(BaseModel):
    """Schema for user login"""
    username: str
    password: str


class UserResponse(BaseModel):
    """Schema for user response (without password)"""
    id: int
    email: str
    username: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class Token(BaseModel):
    """Schema for JWT token response"""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Schema for token payload"""
    user_id: Optional[int] = None