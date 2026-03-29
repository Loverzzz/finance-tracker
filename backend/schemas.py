from pydantic import BaseModel, EmailStr
from typing import List, Optional, Any
from datetime import date, datetime
from decimal import Decimal

# User Schemas
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserOut(BaseModel):
    id: int
    username: str
    email: EmailStr
    created_at: datetime
    class Config:
        from_attributes = True

# Token Schemas
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

# AccountSettings Schemas
class AccountSettingsBase(BaseModel):
    total_gaji: Decimal = Decimal("0.00")
    target_menabung_persen: Decimal = Decimal("0.00")

class AccountSettingsCreate(AccountSettingsBase):
    pass

class AccountSettingsOut(AccountSettingsBase):
    user_id: int
    class Config:
        from_attributes = True

# Transaction Schemas
class TransactionBase(BaseModel):
    tanggal_struk: date
    toko: str
    total_item: int = 1
    items_array: Optional[Any] = None
    category: str
    method: str
    amount: Decimal
    mood: Optional[str] = None
    image_path: Optional[str] = None
    tipe_kirim: Optional[str] = None

class TransactionCreate(TransactionBase):
    pass

class TransactionOut(TransactionBase):
    id: int
    user_id: int
    tanggal_input: datetime
    class Config:
        from_attributes = True

# Budget Schemas
class BudgetBase(BaseModel):
    month: int
    year: int
    needs_target_amount: Decimal = Decimal("0.00")
    wants_target_amount: Decimal = Decimal("0.00")
    savings_target_amount: Decimal = Decimal("0.00")

class BudgetCreate(BudgetBase):
    pass

class BudgetOut(BudgetBase):
    id: int
    user_id: int
    class Config:
        from_attributes = True
