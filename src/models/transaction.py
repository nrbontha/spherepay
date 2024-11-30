from sqlalchemy import Column, Integer, String, Numeric, DateTime, Enum
from sqlalchemy.sql import func
from .base import Base
import enum

class TransactionStatus(enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class Transaction(Base):
    __tablename__ = 'transactions'

    id = Column(Integer, primary_key=True)
    source_currency = Column(String(3), nullable=False)
    target_currency = Column(String(3), nullable=False)
    source_amount = Column(Numeric(precision=20, scale=6), nullable=False)
    target_amount = Column(Numeric(precision=20, scale=6), nullable=False)
    fx_rate = Column(Numeric(precision=20, scale=6), nullable=False)
    margin = Column(Numeric(precision=20, scale=6), nullable=False)
    revenue = Column(Numeric(precision=20, scale=6), nullable=False)
    status = Column(Enum(TransactionStatus), nullable=False, default=TransactionStatus.PENDING)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    settled_at = Column(DateTime(timezone=True)) 