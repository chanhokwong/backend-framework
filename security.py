from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import jwt, JWTError
from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends, HTTPException, status
from sqlmodel import Session, select
from database import get_session
from models import User

# ====== 登入安全部分 ======
# 設置進行加密的實例
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    """加密傳進來的密碼"""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """驗證輸入的密碼和加密的密碼是否一致"""
    return pwd_context.verify(plain_password, hashed_password)

# ====== JWT生成部分 ======
# JWT的組成部分
# Header, Payload, Signature
# Header => ALGORITHM
# Payload => {"sub":"...", "exp":"..."}
# Signature => SECRET_KEY

SECRET_KEY = "your_super_secret_key_123"  # 設置只有自己知道的複雜字串
ALGORITHM = "HS256"  # 算法
ACCESS_TOKEN_EXPIRE_MINUTES = 30  # 有效期(分鐘)

def create_access_token(data: dict, expires_delta: timedelta|None = None):
    """生成JWT"""
    # 基於我們普遍不會修改raw data，所以創建一個變量，再用copy()複製內容
    to_encode = data.copy()

    # 判斷是否傳入通行證有效期時限
    if expires_delta:  # 如果有 則當前時間加上傳入的時間
        expire = datetime.utcnow() + expires_delta
    else:  # 如果沒有傳入 則使用默認設定 當前時間+15mins
        expire = datetime.utcnow() + timedelta(minutes=15)

    # 把計算後的有效期時間傳入到data中，從而組成JWT的Payload
    to_encode.update({"exp": expire})
    # to_encode: {"sub":"...", "exp": "..."}
    encode_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)  # 正式進行jwt編碼
    # JWT (encode_jwt)
    # Header => {"alg": "HS256","typ": "JWT"}
    # Payload => {"sub": "chanhokwong","exp": 1764057770}
    # Signature => a-string-secret-at-least-256-bits-long
    return encode_jwt


# ====== OAuth2部分 ======
# 這行代碼告訴 FastAPI：如果有人要訪問受保護的接口，去哪裡找 Token？
# 答：去 Header 裡找 Authorization: Bearer <token>，如果沒有，就提示去 /users/token 登入
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/token")

async def get_current_user(token: str = Depends(oauth2_scheme), session: Session = Depends(get_session)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="無法驗證憑證",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # 1. 解碼 Token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    # 2. 確保數據庫裡還有這個username (萬一他剛剛被刪號了呢)
    statement = select(User).where(User.username == username)
    user = session.exec(statement).first()
    if user is None:
        raise credentials_exception
    return user
