from datetime import datetime
from pydantic import BaseModel, EmailStr
from typing import Optional

class UserBase(BaseModel):
    name: str
    email: EmailStr

class UserCreate(UserBase):
    password: str  # Add password field

class UserResponse(UserBase):
    id: int

    class Config:
        from_attributes = True

class MessageBase(BaseModel):
    content: str

class MessageCreate(MessageBase):
    pass

# Remove parent_id from MessageResponse
class MessageResponse(MessageBase):
    id: int
    created_at: datetime
    user: UserResponse
    # Removed parent_id field

    class Config:
        from_attributes = True
# token_type: Typically "bearer".
class Token(BaseModel):
    access_token: str
    token_type: str

# this model helps extract the email from the JWT payload.
class TokenData(BaseModel):
    email: Optional[str] = None