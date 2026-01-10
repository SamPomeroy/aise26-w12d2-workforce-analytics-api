from pydantic import BaseModel, EmailStr, Field, validator
from datetime import datetime
from typing import Optional


class UserBase(BaseModel):
    """base user schema with common fields"""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    full_name: Optional[str] = None


class UserCreate(UserBase):
    """schema for user registration"""
    password: str = Field(..., min_length=6, max_length=100)
    role: str = Field(default="user", pattern="^(user|employer|admin)$")
    
    @validator('password')
    def validate_password(cls, v):
        """ensure password meets security requirements"""
        if len(v) < 8:
            raise ValueError('password must be at least 8 characters')
        if not any(char.isdigit() for char in v):
            raise ValueError('password must contain at least one digit')
        if not any(char.isupper() for char in v):
            raise ValueError('password must contain at least one uppercase letter')
        return v


class UserLogin(BaseModel):
    """schema for user login"""
    username: str
    password: str


class UserResponse(UserBase):
    """schema for user response (excludes sensitive data)"""
    id: int
    role: str
    is_active: bool
    is_verified: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class Token(BaseModel):
    """jwt token response"""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """data stored in jwt token"""
    username: Optional[str] = None
    role: Optional[str] = None
