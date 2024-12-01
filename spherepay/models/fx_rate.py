from sqlalchemy import Column, Integer, String, Numeric, DateTime
from ..database import Base

class FxRate(Base):
    __tablename__ = 'fx_rates'

    id = Column(Integer, primary_key=True)
    currency_pair = Column(String(7), nullable=False)
    rate = Column(Numeric(20, 6), nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False) 