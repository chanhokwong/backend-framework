from sqlmodel import create_engine, Session

# 設置SQLite數據庫文件名稱
sqlite_file_name = "database.db"
# 由於python支援SQLite的原因，所以不需要驅動軟件
sqlite_url = f"sqlite:///{sqlite_file_name}"  # 連接數據庫的url
# 創建引擎
engine = create_engine(sqlite_url)

def get_session():
    """連接數據庫，完結時中斷連接"""
    # Session(enginer) => 連接數據庫
    with Session(engine) as session:
        yield session