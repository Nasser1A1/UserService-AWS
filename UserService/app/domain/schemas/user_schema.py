from typing import Optional
from pydantic import BaseModel, Field, EmailStr
from datetime import datetime


# ==============================
# Base Schemas
# ==============================
class UserBase(BaseModel):
    email: EmailStr
    username: Optional[str] = None


# ==============================
# Create Schema (for registration)
# ==============================
class UserCreate(UserBase):
    password: str = Field(..., min_length=6)
    phone_number: Optional[str] = Field(None, max_length=15)
    profile_image_url: Optional[str] = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        schema_extra = {
            "example": {
                "email": "johndoe@example.com",
                "username": "johndoe",
                "password": "StrongPass123!",
                "phone_number": "+12025550123",
                "profile_image_url": "https://example.com/profile.jpg",
            }
        }


# ==============================
# Login Schema

{
  "email": "mahmoud@gmail.com",
  "username": "mahmoud",
  "password": "Mahmoud@1234",
  "phone_number": "+201153453880",
  "profile_image_url": "",
  "created_at": "2025-10-15T00:54:40.272Z",
  "updated_at": "2025-10-15T00:54:40.272Z"
}
# ==============================
class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)

    class Config:
        schema_extra = {
            "example": {
                "email": "johndoe@example.com",
                "password": "StrongPass123!"
            }
        }



class UserNewPassword(BaseModel):
    email: EmailStr
    new_password: str
    session: str
# ==============================
# Update Schema
# ==============================
class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = Field(None, max_length=15)
    profile_image_url: Optional[str] = ""
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        schema_extra = {
            "example": {
                "username": "newname",
                "phone_number": "+12025550199",
                "profile_image_url": "https://example.com/newimage.jpg"
            }
        }


# ==============================
# Output Schema (for responses)
# ==============================
class UserOut(UserBase):
    phone_number: Optional[str] = None
    profile_image_url: Optional[str] = None
    is_active: Optional[bool] = True
    email_verified: Optional[bool] = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True


# ==============================
# Token Schema
# ==============================
class Token(BaseModel):
    access_token: str
    token_type: str

    class Config:
        schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer"
            }
        }
