import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from dotenv import load_dotenv
load_dotenv()
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.staticfiles import StaticFiles
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import timedelta
import models, schemas, crud, auth, database, logic
from pydantic import BaseModel

try:
    models.Base.metadata.create_all(bind=database.engine)
except Exception as e:
    print(f"Database init error: {e}")

app = FastAPI(title="Finance Tracker API")

@app.on_event("startup")
def startup_event():
    try:
        db = database.SessionLocal()
        admin_user = os.getenv("FINTRACK_USER", "reynaldstar")
        admin_pass = os.getenv("FINTRACK_PASS", "reynald123")
        
        if not crud.get_user_by_username(db, admin_user):
            user_data = schemas.UserCreate(username=admin_user, email="admin@local.host", password=admin_pass)
            crud.create_user(db, user_data)
            print(f"[*] Default private admin user '{admin_user}' verified.")
        db.close()
    except Exception as e:
        print(f"Startup user seeding error: {e}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()



@app.post("/login", response_model=schemas.Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    try:
        user = crud.get_user_by_username(db, form_data.username)
        if not user or not auth.verify_password(form_data.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = auth.create_access_token(
            data={"sub": user.username}, expires_delta=access_token_expires
        )
        return {"access_token": access_token, "token_type": "bearer"}
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"DB Error: {str(e)}"
        )

@app.get("/users/me", response_model=schemas.UserOut)
def read_users_me(current_user: models.User = Depends(auth.get_current_user)):
    return current_user

# --- Account Settings ---
@app.get("/settings", response_model=schemas.AccountSettingsOut)
def get_user_settings(db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    settings = crud.get_account_settings(db, current_user.id)
    if not settings:
        raise HTTPException(status_code=404, detail="Settings not found")
    return settings

@app.post("/settings", response_model=schemas.AccountSettingsOut)
def update_user_settings(settings: schemas.AccountSettingsCreate, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    return crud.update_account_settings(db, current_user.id, settings)

# --- Transactions ---
@app.post("/transactions/", response_model=schemas.TransactionOut)
def create_transaction(transaction: schemas.TransactionCreate, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    return crud.create_transaction(db=db, transaction=transaction, user_id=current_user.id)

@app.get("/transactions/", response_model=list[schemas.TransactionOut])
def read_transactions(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    return crud.get_transactions(db, user_id=current_user.id, skip=skip, limit=limit)

@app.put("/transactions/{transaction_id}", response_model=schemas.TransactionOut)
def update_transaction(transaction_id: int, transaction: schemas.TransactionCreate, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    updated = crud.update_transaction(db, transaction_id=transaction_id, user_id=current_user.id, transaction=transaction)
    if not updated:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return updated

@app.delete("/transactions/{transaction_id}")
def delete_transaction(transaction_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    success = crud.delete_transaction(db, transaction_id=transaction_id, user_id=current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return {"detail": "Transaction deleted"}

# --- Budgets ---
@app.post("/budgets/", response_model=schemas.BudgetOut)
def update_budget(budget: schemas.BudgetCreate, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    return crud.create_or_update_budget(db=db, budget=budget, user_id=current_user.id)

@app.get("/budgets/{year}/{month}", response_model=schemas.BudgetOut)
def read_budget(year: int, month: int, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    budget = crud.get_budget(db, user_id=current_user.id, month=month, year=year)
    if budget is None:
        raise HTTPException(status_code=404, detail="Budget not found")
    return budget

# --- Dashboard Logic ---
@app.get("/dashboard/balances")
def get_balances_endpoint(db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    return logic.calculate_balances(db, current_user.id)

@app.get("/dashboard/budget_status/{year}/{month}")
def get_budget_status_endpoint(year: int, month: int, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    return logic.calculate_budget_status(db, current_user.id, month, year)

@app.get("/dashboard/daily_budget")
def get_daily_budget_endpoint(db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    return logic.calculate_daily_budget(db, current_user.id)

@app.get("/dashboard/top_expenses")
def get_top_expenses_endpoint(limit: int = 5, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    return logic.get_top_expenses(db, current_user.id, limit)

@app.get("/dashboard/income/{year}/{month}")
def get_monthly_income_endpoint(year: int, month: int, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    return logic.get_monthly_income(db, current_user.id, month, year)

if not os.getenv("VERCEL"):
    frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend"))
    if os.path.exists(frontend_dir):
        app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")
# Trigger hot-reload
