from sqlmodel import SQLModel, Field
from typing import Optional

# 用戶數據庫模型
# table=True 意昧著數據庫將生成這張表
class User(SQLModel, table=True):
    # 這里設置id為可選字段(如有內容則默認數字)，這是因為寫入數據庫後，它會自動加上id數
    id: Optional[int] = Field(default=None, primary_key=True)
    # 由於每個帳號都應是獨一無二的，所以使用unique屬性
    username: str = Field(index=True, unique=True)
    hashed_password: str

# 用戶注冊模型
# 用於暫時儲存用戶輸入的數據
class UserCreate(SQLModel):
    username: str
    password: str