from decimal import Decimal
from sqlalchemy.orm import Session
from fastapi import HTTPException
from datetime import datetime, UTC

from ..models.fx_rate import FxRate
from ..schemas.fx_rate import FxRateUpdate
from ..logger import logger


class FxRateService:
    def __init__(self, db: Session):
        self.db = db

    def create_rate(self, rate_update: FxRateUpdate) -> FxRate:
        try:
            fx_rate = FxRate(
                currency_pair=rate_update.pair,
                rate=Decimal(rate_update.rate),
                timestamp=rate_update.timestamp
            )
            self.db.add(fx_rate)
            self.db.commit()
            logger.info(f"Created new FX rate: {rate_update.pair} = {rate_update.rate}")
            return fx_rate

        except Exception as e:
            logger.error(f"Error creating FX rate: {str(e)}")
            self.db.rollback()
            raise

    def get_latest_rate(self, base: str, quote: str) -> FxRate:
        try:
            pair = f"{base}/{quote}"
            rate = self.db.query(FxRate)\
                .filter(FxRate.currency_pair == pair)\
                .order_by(FxRate.timestamp.desc())\
                .first()
            
            if not rate:
                logger.error(f"No FX rate found for pair: {pair}")
                raise HTTPException(
                    status_code=404, 
                    detail=f"No rate available for {pair}"
                )
                
            if (datetime.now(UTC) - rate.timestamp).seconds > 300:  # 5 minutes
                logger.warning(f"FX rate for {pair} is stale: {rate.timestamp}")
                
            return rate
            
        except Exception as e:
            logger.error(f"Error fetching FX rate: {str(e)}")
            raise