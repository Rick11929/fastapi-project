from sqlalchemy import create_engine, text
import time

def test_db_connection(retries=5):
    # 数据库连接URL
    DATABASE_URL = "postgresql://fastapi_user:your_password@localhost:5432/fastapi_db"
    
    for attempt in range(retries):
        try:
            print(f"\n尝试连接数据库... (第 {attempt + 1} 次)")
            
            # 创建数据库引擎
            engine = create_engine(DATABASE_URL)
            
            # 尝试建立连接并执行简单查询
            with engine.connect() as connection:
                result = connection.execute(text("SELECT version()"))
                version = result.scalar()
                
                print("✅ 数据库连接成功！")
                print(f"PostgreSQL 版本: {version}")
                
                # 测试数据库读写
                print("\n测试数据库读写能力...")
                
                # 创建测试表
                connection.execute(text("""
                    CREATE TABLE IF NOT EXISTS connection_test (
                        id SERIAL PRIMARY KEY,
                        test_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """))
                
                # 插入数据
                connection.execute(text("INSERT INTO connection_test DEFAULT VALUES"))
                connection.commit()
                
                # 读取数据
                result = connection.execute(text("SELECT COUNT(*) FROM connection_test"))
                count = result.scalar()
                print(f"✅ 数据库读写测试成功！当前测试表中有 {count} 条记录")
                
                return True
                
        except Exception as e:
            print(f"❌ 连接失败: {str(e)}")
            if attempt < retries - 1:
                wait_time = 2 ** attempt  # 指数退避
                print(f"等待 {wait_time} 秒后重试...")
                time.sleep(wait_time)
            else:
                print("\n❌ 达到最大重试次数，连接失败")
                return False

if __name__ == "__main__":
    print("开始数据库连接测试...")
    test_db_connection() 