from sqlalchemy.orm import Session
import models, schemas
from auth import get_password_hash

# --- User CRUD ---
def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = get_password_hash(user.password)
    db_user = models.User(username=user.username, email=user.email, password_hash=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # Create default empty account settings
    db_settings = models.AccountSettings(user_id=db_user.id)
    db.add(db_settings)
    db.commit()
    
    return db_user

# --- Account Settings CRUD ---
def get_account_settings(db: Session, user_id: int):
    return db.query(models.AccountSettings).filter(models.AccountSettings.user_id == user_id).first()

def update_account_settings(db: Session, user_id: int, settings: schemas.AccountSettingsCreate):
    db_settings = get_account_settings(db, user_id)
    if db_settings:
        db_settings.total_gaji = settings.total_gaji
        db_settings.target_menabung_persen = settings.target_menabung_persen
        db.commit()
        db.refresh(db_settings)
    return db_settings

# --- Transaction CRUD ---
def get_transactions(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    return db.query(models.Transaction).filter(models.Transaction.user_id == user_id).order_by(models.Transaction.tanggal_struk.desc()).offset(skip).limit(limit).all()

def create_transaction(db: Session, transaction: schemas.TransactionCreate, user_id: int):
    # Ensure amount is treated properly and saved
    db_transaction = models.Transaction(**transaction.model_dump(), user_id=user_id)
    db.add(db_transaction)
    db.commit()
    db.refresh(db_transaction)
    return db_transaction

def update_transaction(db: Session, transaction_id: int, user_id: int, transaction: schemas.TransactionCreate):
    db_transaction = db.query(models.Transaction).filter(models.Transaction.id == transaction_id, models.Transaction.user_id == user_id).first()
    if db_transaction:
        for key, value in transaction.model_dump().items():
            setattr(db_transaction, key, value)
        db.commit()
        db.refresh(db_transaction)
    return db_transaction

def delete_transaction(db: Session, transaction_id: int, user_id: int):
    db_transaction = db.query(models.Transaction).filter(models.Transaction.id == transaction_id, models.Transaction.user_id == user_id).first()
    if db_transaction:
        db.delete(db_transaction)
        db.commit()
        return True
    return False

# --- Budget CRUD ---
def get_budget(db: Session, user_id: int, month: int, year: int):
    return db.query(models.Budget).filter(models.Budget.user_id == user_id, models.Budget.month == month, models.Budget.year == year).first()

def create_or_update_budget(db: Session, budget: schemas.BudgetCreate, user_id: int):
    db_budget = get_budget(db, user_id, budget.month, budget.year)
    if db_budget:
        db_budget.needs_target_amount = budget.needs_target_amount
        db_budget.wants_target_amount = budget.wants_target_amount
        db_budget.savings_target_amount = budget.savings_target_amount
    else:
        db_budget = models.Budget(**budget.model_dump(), user_id=user_id)
        db.add(db_budget)
    
    db.commit()
    db.refresh(db_budget)
    return db_budget
