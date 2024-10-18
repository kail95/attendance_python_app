from pydantic import BaseModel

class AdminCreate(BaseModel):
    email: str
    dep_name: int
    is_super_admin: bool = False  # Default to non-super admin

    class Config:
        orm_mode = True

class Token(BaseModel):
    access_token: str
    token_type: str
