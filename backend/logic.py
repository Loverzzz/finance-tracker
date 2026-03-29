from sqlalchemy.orm import Session
from sqlalchemy import func, extract
import models
from datetime import datetime
import calendar

def calculate_balances(db: Session, user_id: int):
    # Get total gaji from account settings
    settings = db.query(models.AccountSettings).filter(models.AccountSettings.user_id == user_id).first()
    total_gaji = float(settings.total_gaji) if settings else 0.0
    
    # Simple logic: assume gaji is kept in Mandiri.
    total_mandiri = total_gaji
    total_cash = 0.0
    
    transactions = db.query(models.Transaction).filter(models.Transaction.user_id == user_id).all()
    
    for t in transactions:
        amount = float(t.amount)
        tipe_kirim = t.tipe_kirim.lower() if t.tipe_kirim else ""
        method = t.method.lower() if t.method else ""
        category = t.category.lower() if t.category else ""
        
        if tipe_kirim == 'pemasukan':
            if method == 'mandiri':
                total_mandiri += amount
            elif method == 'cash':
                total_cash += amount
        elif tipe_kirim == 'pengeluaran':
            if method == 'mandiri':
                total_mandiri -= amount
            elif method == 'cash':
                total_cash -= amount
        elif tipe_kirim == 'transfer':
            if 'tarik' in category:
                total_mandiri -= amount
                total_cash += amount
            elif 'setor' in category:
                total_cash -= amount
                total_mandiri += amount

    return {
        "total_money": total_mandiri + total_cash,
        "total_mandiri": total_mandiri,
        "total_cash": total_cash
    }

def calculate_budget_status(db: Session, user_id: int, month: int, year: int):
    budget = db.query(models.Budget).filter(
        models.Budget.user_id == user_id,
        models.Budget.month == month,
        models.Budget.year == year
    ).first()
    
    needs_goal = float(budget.needs_target_amount) if budget else 0.0
    wants_goal = float(budget.wants_target_amount) if budget else 0.0
    savings_goal = float(budget.savings_target_amount) if budget else 0.0
    
    expenses = db.query(
        models.Transaction.category,
        func.sum(models.Transaction.amount).label('total_spent')
    ).filter(
        models.Transaction.user_id == user_id,
        extract('month', models.Transaction.tanggal_struk) == month,
        extract('year', models.Transaction.tanggal_struk) == year,
        func.lower(models.Transaction.tipe_kirim) == 'pengeluaran'
    ).group_by(models.Transaction.category).all()
    
    needs_spent = 0.0
    wants_spent = 0.0
    savings_spent = 0.0
    
    for category, total in expenses:
        cat_lower = category.lower() if category else ""
        if 'need' in cat_lower:
            needs_spent += float(total)
        elif 'want' in cat_lower:
            wants_spent += float(total)
        elif 'saving' in cat_lower or 'tabung' in cat_lower:
            savings_spent += float(total)
        else:
            # Default to wants if unknown
            wants_spent += float(total)
            
    total_goal = needs_goal + wants_goal
    total_spent = needs_spent + wants_spent
    
    status = "aman"
    if total_goal > 0:
        if total_spent > total_goal:
            status = "over_budget"
        elif total_spent > (total_goal * 0.8):
            status = "potensi_over_budget"
            
    return {
        "needs_spent": needs_spent,
        "needs_goal": needs_goal,
        "wants_spent": wants_spent,
        "wants_goal": wants_goal,
        "savings_spent": savings_spent,
        "savings_goal": savings_goal,
        "status": status,
        "total_goal": total_goal,
        "total_spent": total_spent
    }

def calculate_daily_budget(db: Session, user_id: int):
    now = datetime.now()
    month = now.month
    year = now.year
    day = now.day
    
    _, last_day = calendar.monthrange(year, month)
    days_left = last_day - day + 1
    
    budget_status = calculate_budget_status(db, user_id, month, year)
    
    remaining_budget = budget_status['total_goal'] - budget_status['total_spent']
    
    daily_budget = 0.0
    if remaining_budget > 0 and days_left > 0:
        daily_budget = remaining_budget / days_left
        
    return {
        "month": month,
        "year": year,
        "remaining_budget": remaining_budget,
        "days_left": days_left,
        "daily_budget": daily_budget
    }

def get_top_expenses(db: Session, user_id: int, limit: int = 5):
    now = datetime.now()
    month = now.month
    year = now.year
    
    top_toko = db.query(
        models.Transaction.toko,
        models.Transaction.category,
        func.sum(models.Transaction.amount).label('total_spent')
    ).filter(
        models.Transaction.user_id == user_id,
        extract('month', models.Transaction.tanggal_struk) == month,
        extract('year', models.Transaction.tanggal_struk) == year,
        func.lower(models.Transaction.tipe_kirim) == 'pengeluaran'
    ).group_by(models.Transaction.toko, models.Transaction.category).order_by(
        func.sum(models.Transaction.amount).desc()
    ).limit(limit).all()
    
    return [{"toko": t[0], "category": t[1], "amount": float(t[2])} for t in top_toko]

def get_monthly_income(db: Session, user_id: int, month: int, year: int):
    income = db.query(
        func.sum(models.Transaction.amount)
    ).filter(
        models.Transaction.user_id == user_id,
        extract('month', models.Transaction.tanggal_struk) == month,
        extract('year', models.Transaction.tanggal_struk) == year,
        func.lower(models.Transaction.tipe_kirim) == 'pemasukan'
    ).scalar()
    
    return {"total_income": float(income or 0.0)}
