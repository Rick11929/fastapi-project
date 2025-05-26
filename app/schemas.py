from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List

class Item(BaseModel):
    name: str = Field(..., min_length=1, max_length=50, description="商品名称")
    price: float = Field(..., gt=0, description="商品价格")
    description: Optional[str] = Field(None, max_length=200, description="商品描述")
    is_available: bool = Field(default=True, description="是否可用")
    id: Optional[int] = None

    class Config:
        from_attributes = True  # 替换原来的 orm_mode = True

class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    full_name: Optional[str] = None

class UserCreate(UserBase):
    password: str = Field(..., min_length=6)

class User(UserBase):
    id: int
    is_active: bool = True
    items: List[Item] = []

    class Config:
        from_attributes = True  # 替换原来的 orm_mode = True

class Token(BaseModel):
    access_token: str
    token_type: str