from fastapi import FastAPI, Query, Path, Body, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from typing import List
from datetime import timedelta
from .schemas import Item, User, UserCreate, Token
from .dependencies import (
    get_current_user, 
    create_access_token, 
    ACCESS_TOKEN_EXPIRE_MINUTES,
    get_db  # 从 dependencies 导入
)
from sqlalchemy.orm import Session
from . import models, database
from .database import engine, get_db


app = FastAPI(
    title="高级FastAPI示例",
    description="包含认证和依赖注入的API示例",
    version="2.0.0"
)

# 创建数据库表
models.Base.metadata.create_all(bind=engine)

@app.get("/")
async def root():
    return {"message": "欢迎使用 FastAPI!"}

@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"你好 {name}"}

@app.get("/items/", response_model=List[Item])
async def get_items(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    items = db.query(models.Item).offset(skip).limit(limit).all()
    return items

@app.post("/items/", response_model=Item)
async def create_item(
    item: Item,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    db_item = models.Item(
        name=item.name,
        price=item.price,
        description=item.description,
        is_available=item.is_available,
        owner_id=current_user.id
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

@app.get("/items/{item_id}", response_model=Item)
async def get_item(
    item_id: int = Path(..., ge=0, description="商品ID"),
    db: Session = Depends(get_db)
):
    item = db.query(models.Item).filter(models.Item.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="商品未找到")
    return item

@app.put("/items/{item_id}", response_model=Item)
async def update_item(
    item_id: int = Path(..., ge=0),
    item: Item = Body(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    db_item = db.query(models.Item).filter(
        models.Item.id == item_id,
        models.Item.owner_id == current_user.id
    ).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="商品未找到")
    
    for field, value in item.dict(exclude_unset=True).items():
        setattr(db_item, field, value)
    
    db.commit()
    db.refresh(db_item)
    return db_item

@app.delete("/items/{item_id}")
async def delete_item(
    item_id: int = Path(..., ge=0),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    db_item = db.query(models.Item).filter(
        models.Item.id == item_id,
        models.Item.owner_id == current_user.id
    ).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="商品未找到")
    
    db.delete(db_item)
    db.commit()
    return {"message": f"商品 '{db_item.name}' 已删除"}

@app.get("/items/search/", response_model=List[Item])
async def search_items(
    keyword: str = Query(None, min_length=1, description="搜索关键词"),
    min_price: float = Query(None, ge=0, description="最低价格"),
    max_price: float = Query(None, ge=0, description="最高价格"),
    db: Session = Depends(get_db)
):
    query = db.query(models.Item)
    
    if keyword:
        query = query.filter(models.Item.name.ilike(f"%{keyword}%"))
    if min_price is not None:
        query = query.filter(models.Item.price >= min_price)
    if max_price is not None:
        query = query.filter(models.Item.price <= max_price)
        
    return query.all()

@app.get("/users/me/items/", response_model=List[Item])
async def read_user_items(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return db.query(models.Item).filter(models.Item.owner_id == current_user.id).all()
@app.get("/items/{item_id}", response_model=Item)
async def get_item(
    item_id: int = Path(..., ge=0, description="商品ID"),
):
    if item_id >= len(items_db):
        raise HTTPException(status_code=404, detail="商品未找到")
    return items_db[item_id]

@app.put("/items/{item_id}", response_model=Item)
async def update_item(
    item_id: int = Path(..., ge=0),
    item: Item = Body(...),
):
    if item_id >= len(items_db):
        raise HTTPException(status_code=404, detail="商品未找到")
    items_db[item_id] = item
    return item

@app.delete("/items/{item_id}")
async def delete_item(item_id: int = Path(..., ge=0)):
    if item_id >= len(items_db):
        raise HTTPException(status_code=404, detail="商品未找到")
    deleted_item = items_db.pop(item_id)
    return {"message": f"商品 '{deleted_item.name}' 已删除"}

@app.get("/items/search/", response_model=List[Item])
async def search_items(
    keyword: str = Query(None, min_length=1, description="搜索关键词"),
    min_price: float = Query(None, ge=0, description="最低价格"),
    max_price: float = Query(None, ge=0, description="最高价格"),
):
    results = items_db
    
    if keyword:
        results = [item for item in results if keyword.lower() in item.name.lower()]
    if min_price is not None:
        results = [item for item in results if item.price >= min_price]
    if max_price is not None:
        results = [item for item in results if item.price <= max_price]
        
    return results

# 用户注册
@app.post("/users/", response_model=User)
async def create_user(user: UserCreate, db: Session = Depends(get_db)):
    # 检查用户名是否已存在
    db_user = db.query(models.User).filter(models.User.username == user.username).first()
    if db_user:
        raise HTTPException(
            status_code=400,
            detail="用户名已存在"
        )
    
    # 创建新用户
    db_user = models.User(
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        hashed_password=user.password  # 注意：实际应用中应该对密码进行哈希处理
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user
    if user.username in fake_users_db:
        raise HTTPException(
            status_code=400,
            detail="用户名已存在"
        )
    # 在实际应用中应该对密码进行哈希处理
    fake_users_db[user.username] = {
        "id": len(fake_users_db) + 1,
        **user.dict(),
        "items": []
    }
    return fake_users_db[user.username]

# 登录获取令牌
@app.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    # 从数据库查询用户
    user = db.query(models.User).filter(models.User.username == form_data.username).first()
    if not user or user.hashed_password != form_data.password:  # 实际应用中应该使用安全的密码验证
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# 获取当前用户信息
@app.get("/users/me/", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

# 为当前用户添加商品
@app.post("/users/me/items/", response_model=Item)
async def create_item_for_user(
    item: Item,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db_item = models.Item(
        name=item.name,
        price=item.price,
        description=item.description,
        is_available=item.is_available,
        owner_id=current_user.id
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

# 获取当前用户的所有商品
@app.get("/users/me/items/", response_model=List[Item])
async def read_user_items(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return db.query(models.Item).filter(models.Item.owner_id == current_user.id).all()