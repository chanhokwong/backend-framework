from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from models import UserCreate, User
from sqlmodel import Session, select
from database import get_session
from security import get_password_hash, verify_password, ACCESS_TOKEN_EXPIRE_MINUTES, create_access_token
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
import time

# 設置APIRouter
# api為/users => http://localhost/users
router = APIRouter(
    prefix="/users",
    tags=["Users"]
)

def send_welcome_email(email_to: str):
    print(f"正在發送郵件給 {email_to}...")
    time.sleep(3)
    print(f"郵件已發送給 {email_to}!")

# ====== 用戶注冊功能 ======
# 設置路由為http://localhost/users/register
# 返回的數據類型為models文件中設置的User數據模型
# 請求類型為post
@router.post("/register", response_model=User)
async def register(
        user_in: UserCreate,
        background_tasks: BackgroundTasks,  # BackgroundTasks是異步任務的實例，讓函數可以把一些需要時間運行的函數異步執行
        session: Session = Depends(get_session),  # session用於連接數據庫，於函數結束後會中止連接
):
    # 搜尋注冊的用戶名是否已存在
    # 1. 生成SQL指令
    statement = select(User).where(User.username == user_in.username)
    # 2. 執行生成的SQL指令
    existing_user = session.exec(statement).first()

    # 3. 判斷是否找到用戶名
    if existing_user:  # 如果找到用戶名
        # 返回下列錯誤信息給用戶 400 Username already registered
        raise HTTPException(status_code=400, detail="Username already registered")

    # 如果找不到數據庫存在該用戶名
    # 1. 加密用戶輸入的密碼
    hashed_pwd = get_password_hash(user_in.password)

    # 2. 把用戶輸入的用戶名和加密的密碼套入到User數據模型中
    new_user = User(
        username=user_in.username,
        hashed_password=hashed_pwd,
    )

    # 通過session來添加一則User數據模型的數據
    session.add(new_user)
    # 正式提交請求至數據庫
    session.commit()
    # 更新數據庫，以讓new_user變量獲取id
    # new_user => {"id": 0, "username": "admin", "hashed_password":"..."}
    session.refresh(new_user)

    # 異步執行任務
    # 為了讓發送注冊成功郵件的過程不堵塞注冊的時間，
    # 因而把其作為異步任務，讓系統先返回任務完成的提示給用戶，
    # 然後後台再執行剩餘的發送郵件任務
    # send_welcome_email是函數
    # "chanhokwong718@gmail.com"則是send_welcome_email函數的傳參 可指定屬性名 如 email_to="chanhokwong718@gmail.com"
    background_tasks.add_task(send_welcome_email, "chanhokwong718@gmail.com")

    return new_user

# ====== 用戶登入功能 ======
# 設置路由為http://localhost/users/register
# 請求類型為post
@router.post("/token")
async def login_for_access_token(
        form_data: OAuth2PasswordRequestForm = Depends(),  # 登入多數以form的形式提交數據，這裹以OAuth2PasswordRequestForm的形式作為輸入
        session: Session = Depends(get_session)  # session用於連接數據庫，於函數結束後會中止連接
):
    # 驗證用戶名以及密碼是否與數據庫的數據一致
    # 1. 設置指令，指令為檢索數據庫中的User表，是否有username字段的數據與用戶輸入的username一致
    # 注意：OAuth2PasswordRequestForm 會自動把參數解析到 form_data.username 和 form_data.password
    statement = select(User).where(User.username == form_data.username)
    # 2. 執行上面的數據庫指令，並用first()提取第一個匹配值
    user = session.exec(statement).first()

    # 3. 如果user的值為空 或者 輸入密碼與數據庫中的密碼不一致
    if not user or not verify_password(form_data.password, user.hashed_password):
        # 返回錯誤 401 用戶名或密碼錯誤
        raise HTTPException(
            status_code=401,
            detail="用戶名或密碼錯誤",
            headers={"WWW-Authenticate": "Bearer"}
        )

    # 如果用戶名和密碼都驗證成功，便需考慮JWT的構建
    # 這裹主要是傳入JWT的Payload部分

    # 計算通行證有效的時間，timedelta會將時間轉換成秒
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    # create_access_token為security.py中定義的函數
    # 其將返回完整的access_token
    access_token = create_access_token(
        data={"sub": user.username},  # data用於Payload的一部分
        expires_delta=access_token_expires  # expires_delta用於計算通行證的到期時間
    )

    # 返回標準格式的 Token 信息
    return {"access_token": access_token, "token_type": "bearer"}