import pytest
from fastapi.testclient import TestClient
from main import app
from sqlmodel import create_engine, SQLModel, Session
from sqlmodel.pool import StaticPool
from database import get_session

# ====== 數據庫測試配置 ======
# 測試用的數據庫url
# 使用 SQLite 內存模式 (sqlite:///:memory:)，速度快且測試完自動消失，不留痕跡
# StaticPool 是為了讓內存數據庫在多個線程中共享
TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)

# Pytest Fixture: 每次測試前執行
# 這個函數會負責：創建表 -> 測試 -> 刪除表
@pytest.fixture(name="session")
def session_fixture():
    # 創建表
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    # 測試結束後，刪除所有表 (其實內存數據庫關閉就沒了，但這樣寫更保險)
    SQLModel.metadata.drop_all(engine)

# Pytest Fixture: 配置 TestClient
@pytest.fixture(name="client")
def client_fixture(session: Session):
    # 定義一個臨時的 get_session 函數，讓它返回我們上面創建的測試 session
    def get_session_override():
        return session

    # 告訴 app：凡是用到 get_session 的地方，都換成 get_session_override
    app.dependency_overrides[get_session] = get_session_override

    client = TestClient(app)
    yield client

    # 測試結束後，清除覆蓋，還原 app 狀態
    app.dependency_overrides.clear()

# ====== 編寫測試用例 ======
def test_register(client: TestClient):
    response = client.post("users/register", json={"username": "testuser", "password": "password"})
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "testuser"
    assert "hashed_password" in data
    assert "id" in data

