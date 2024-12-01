from decimal import Decimal
from sqlalchemy.orm import Session
from fastapi import HTTPException

from ..models.fx_rate import FxRate
from ..schemas.fx_rate import FxRateUpdate, SUPPORTED_CURRENCIES

class FxRateService:
    def __init__(self, db: Session):
        self.db = db

    def create_rate(self, rate_update: FxRateUpdate) -> FxRate:
        try:
            rate_decimal = Decimal(rate_update.rate)
            fx_rate = FxRate(
                currency_pair=rate_update.pair,
                rate=rate_decimal,
                timestamp=rate_update.timestamp
            )
            
            self.db.add(fx_rate)
            self.db.commit()
            
            return fx_rate
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=400, detail=str(e))

    def get_latest_rate(self, base: str, quote: str) -> FxRate:
        if base not in SUPPORTED_CURRENCIES or quote not in SUPPORTED_CURRENCIES:
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported currency pair. Supported currencies: {', '.join(SUPPORTED_CURRENCIES)}"
            )
        
        pair = f"{base}/{quote}"
        latest_rate = self.db.query(FxRate)\
            .filter(FxRate.currency_pair == pair)\
            .order_by(FxRate.timestamp.desc())\
            .first()
            
        if not latest_rate:
            raise HTTPException(status_code=404, detail=f"No rate found for pair {pair}")
            
        return latest_rate 