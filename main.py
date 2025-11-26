from fastapi import FastAPI
from sqlmodel import SQLModel
from database import engine
from routers import users
from fastapi.middleware.cors import CORSMiddleware
app = FastAPI()  # FastAPI實例化

# 設置後端白名單 CORS
# 讓名單中的IP能夠存取後端的服務
origins = [
    "http://localhost",
    "http://127.0.0.1:3000",
    "*"
]

# 往FastAPI實例中新增中間件設置
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # 套用白名單
    allow_credentials=True,
    allow_methods=["*"],  # *是允許get,post,put,...方法的存取
    allow_headers=["*"],
)

# @app.on_event 指每次後端即app這個FastAPI重啟時
@app.on_event("startup")
def startup():
    # 創建所有繼承了SQLModel的表
    SQLModel.metadata.create_all(engine)

app.include_router(users.router)  # 設置routers文件夾中的users中的APIRouter(變量: router)

@app.get("/")  # 設置http://localhost的get存取函數
async def root():
    return {"message": "歡迎來到圖書管理系統"}