import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import Base
from app.dependencies import get_db
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from dotenv import load_dotenv
load_dotenv()

# 数据库配置
DB_USER = "fastapi_user"
DB_PASSWORD = "your_password"
DB_HOST = "localhost"
DB_PORT = "5432"
TEST_DB_NAME = "test_fastapi_db"

# 创建测试数据库的连接URL
SQLALCHEMY_DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{TEST_DB_NAME}"

def create_test_database():
    """创建测试数据库"""
    # 连接到默认的 postgres 数据库
    conn = psycopg2.connect(
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT,
        database="postgres"
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()
    
    # 先尝试删除已存在的测试数据库
    try:
        cur.execute(f"DROP DATABASE IF EXISTS {TEST_DB_NAME}")
        print(f"删除已存在的测试数据库 {TEST_DB_NAME}")
    except Exception as e:
        print(f"删除数据库时出错: {e}")
    
    # 创建新的测试数据库
    try:
        cur.execute(f"CREATE DATABASE {TEST_DB_NAME}")
        print(f"创建新的测试数据库 {TEST_DB_NAME}")
    except Exception as e:
        print(f"创建数据库时出错: {e}")
    finally:
        cur.close()
        conn.close()

# 创建测试数据库引擎
engine = create_engine(SQLALCHEMY_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 重写依赖
def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

def setup_module(module):
    """测试模块开始前执行"""
    print("\n=== 开始测试：创建数据库和表 ===")
    create_test_database()  # 先创建测试数据库
    Base.metadata.create_all(bind=engine)  # 然后创建表

def teardown_module(module):
    """测试模块结束后执行"""
    print("\n=== 测试结束：清理数据库 ===")
    Base.metadata.drop_all(bind=engine)
    
    # 删除测试数据库
    conn = psycopg2.connect(
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT,
        database="postgres"
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()
    try:
        cur.execute(f"DROP DATABASE IF EXISTS {TEST_DB_NAME}")
        print(f"删除测试数据库 {TEST_DB_NAME}")
    except Exception as e:
        print(f"删除数据库时出错: {e}")
    finally:
        cur.close()
        conn.close()

# 基础API测试
def test_read_main():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "欢迎使用 FastAPI!"}

def test_say_hello():
    response = client.get("/hello/测试用户")
    assert response.status_code == 200
    assert response.json() == {"message": "你好 测试用户"}

# 用户相关测试
def test_create_user():
    response = client.post(
        "/users/",
        json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpass123",
            "full_name": "Test User"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "testuser"
    assert data["email"] == "test@example.com"
    assert "id" in data

def test_create_duplicate_user():
    # 创建第一个用户
    client.post(
        "/users/",
        json={
            "username": "testuser2",
            "email": "test2@example.com",
            "password": "testpass123",
            "full_name": "Test User 2"
        }
    )
    # 尝试创建重复用户
    response = client.post(
        "/users/",
        json={
            "username": "testuser2",
            "email": "test3@example.com",
            "password": "testpass123",
            "full_name": "Test User 3"
        }
    )
    assert response.status_code == 400
    assert "用户名已存在" in response.json()["detail"]

# 认证相关测试
def test_login():
    # 先创建用户
    client.post(
        "/users/",
        json={
            "username": "loginuser",
            "email": "login@example.com",
            "password": "testpass123",
            "full_name": "Login User"
        }
    )
    # 测试登录
    response = client.post(
        "/token",
        data={
            "username": "loginuser",
            "password": "testpass123"
        }
    )
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"

def get_test_token():
    # 创建测试用户并获取token
    response = client.post(
        "/users/",
        json={
            "username": f"testuser_{os.urandom(4).hex()}",  # 生成随机用户名避免冲突
            "email": f"test_{os.urandom(4).hex()}@example.com",
            "password": "testpass123",
            "full_name": "Test User"
        }
    )
    
    if response.status_code != 200:
        print(f"用户创建失败: {response.json()}")  # 添加调试信息
        raise Exception("用户创建失败")
    
    # 获取token
    response = client.post(
        "/token",
        data={
            "username": response.json()["username"],  # 使用返回的用户名
            "password": "testpass123"
        }
    )
    
    if response.status_code != 200:
        print(f"Token获取失败: {response.json()}")  # 添加调试信息
        raise Exception("Token获取失败")
        
    return response.json()["access_token"]
    response = client.post(
        "/users/",
        json={
            "username": "itemuser",
            "email": "item@example.com",
            "password": "testpass123",
            "full_name": "Item User"
        }
    )
    
    # 确保用户创建成功
    assert response.status_code == 200
    
    # 获取token
    response = client.post(
        "/token",
        data={
            "username": "itemuser",
            "password": "testpass123"
        }
    )
    assert response.status_code == 200
    return response.json()["access_token"]

# 商品相关测试
def test_create_item():
    token = get_test_token()
    response = client.post(
        "/items/",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "测试商品",
            "price": 99.9,
            "description": "这是一个测试商品",
            "is_available": True
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "测试商品"
    assert data["price"] == 99.9
    assert "id" in data

def test_get_items():
    token = get_test_token()
    # 先创建一些商品
    client.post(
        "/items/",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "商品1",
            "price": 99.9,
            "description": "描述1",
            "is_available": True
        }
    )
    
    response = client.get("/items/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0

def test_search_items():
    token = get_test_token()
    # 创建测试商品
    client.post(
        "/items/",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "高价商品",
            "price": 999.9,
            "description": "这是一个高价商品",
            "is_available": True
        }
    )
    
    # 测试搜索功能
    response = client.get("/items/search/?keyword=高价&min_price=500")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert any(item["name"] == "高价商品" for item in data)

def test_get_user_items():
    token = get_test_token()
    # 先为用户创建一个商品
    client.post(
        "/users/me/items/",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "用户商品",
            "price": 88.8,
            "description": "这是用户的商品",
            "is_available": True
        }
    )
    
    # 获取用户的商品列表
    response = client.get(
        "/users/me/items/",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0

