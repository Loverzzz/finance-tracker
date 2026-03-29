from sqlalchemy import Column, Integer, String, DECIMAL, Date, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.types import TIMESTAMP
from database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())

    settings = relationship("AccountSettings", back_populates="user", uselist=False, cascade="all, delete-orphan")
    transactions = relationship("Transaction", back_populates="user", cascade="all, delete-orphan")
    budgets = relationship("Budget", back_populates="user", cascade="all, delete-orphan")

class AccountSettings(Base):
    __tablename__ = "account_settings"
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    total_gaji = Column(DECIMAL(15, 2), default=0.00)
    target_menabung_persen = Column(DECIMAL(5, 2), default=0.00)

    user = relationship("User", back_populates="settings")

class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    tanggal_input = Column(TIMESTAMP, server_default=func.now())
    tanggal_struk = Column(Date, nullable=False)
    toko = Column(String(255), nullable=False)
    total_item = Column(Integer, default=1)
    items_array = Column(JSON)
    category = Column(String(100), nullable=False)
    method = Column(String(100), nullable=False)
    amount = Column(DECIMAL(15, 2), nullable=False)
    mood = Column(String(50))
    image_path = Column(String(255))
    tipe_kirim = Column(String(50))

    user = relationship("User", back_populates="transactions")

class Budget(Base):
    __tablename__ = "budgets"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    month = Column(Integer, nullable=False)
    year = Column(Integer, nullable=False)
    needs_target_amount = Column(DECIMAL(15, 2), default=0.00)
    wants_target_amount = Column(DECIMAL(15, 2), default=0.00)
    savings_target_amount = Column(DECIMAL(15, 2), default=0.00)

    user = relationship("User", back_populates="budgets")
