from sqlalchemy import Column, String, Numeric, DateTime
from sqlalchemy.sql import func
from .base import Base

class LiquidityPool(Base):
    __tablename__ = 'liquidity_pools'

    currency = Column(String(3), primary_key=True)
    balance = Column(Numeric(precision=20, scale=6), nullable=False)
    reserved_balance = Column(Numeric(precision=20, scale=6), nullable=False, default=0)
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()) 