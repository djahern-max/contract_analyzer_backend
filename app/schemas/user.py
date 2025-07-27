from pydantic import BaseModel, EmailStr
from typing import List

class UserCreate(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    email: EmailStr 

    class config:
        orm_mode = True

class UserListResponse(BaseModel):
    users: List[UserResponse]

    
