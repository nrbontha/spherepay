from sqlalchemy import Column, Integer, String, Numeric, DateTime, Index
from sqlalchemy.sql import func
from .base import Base

class FxRate(Base):
    __tablename__ = 'fx_rates'

    id = Column(Integer, primary_key=True)
    currency_pair = Column(String(7), nullable=False)  # Format: "USD/EUR"
    rate = Column(Numeric(precision=20, scale=6), nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (
        Index('ix_fx_rates_currency_pair_timestamp', currency_pair, timestamp),
    ) 