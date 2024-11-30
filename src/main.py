from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, validator
from datetime import datetime
from decimal import Decimal, InvalidOperation
from sqlalchemy.orm import Session

from .database import get_db
from .models.fx_rate import FxRate

app = FastAPI()

SUPPORTED_CURRENCIES = {'USD', 'EUR', 'JPY', 'GBP', 'AUD'}

class FxRateUpdate(BaseModel):
    pair: str
    rate: str
    timestamp: datetime

    @validator('pair')
    def validate_currency_pair(cls, pair):
        try:
            base, quote = pair.split('/')
            if base not in SUPPORTED_CURRENCIES or quote not in SUPPORTED_CURRENCIES:
                raise ValueError(
                    f"Currency pair {pair} contains unsupported currency. "
                    f"Supported currencies: {', '.join(SUPPORTED_CURRENCIES)}"
                )
            return pair
        except ValueError as e:
            raise ValueError(f"Invalid currency pair format. Error: {str(e)}")

    @validator('rate')
    def validate_rate(cls, rate):
        try:
            rate_decimal = Decimal(rate)
            if rate_decimal <= 0:
                raise ValueError("Rate must be positive")
            return rate
        except (ValueError, InvalidOperation) as e:
            raise ValueError(f"Invalid rate format: {str(e)}")


@app.post("/fx-rate")
async def update_fx_rate(rate_update: FxRateUpdate, db: Session = Depends(get_db)):
    try:
        rate_decimal = Decimal(rate_update.rate)
        
        fx_rate = FxRate(
            currency_pair=rate_update.pair,
            rate=rate_decimal,
            timestamp=rate_update.timestamp
        )
        
        db.add(fx_rate)
        db.commit()
        
        return {
            "status": "success",
            "data": {
                "pair": fx_rate.currency_pair,
                "rate": str(fx_rate.rate),
                "timestamp": fx_rate.timestamp
            }
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/fx-rate/{base}-{quote}")
async def get_latest_rate(base: str, quote: str, db: Session = Depends(get_db)):
    try:
        pair = f"{base}/{quote}"
        if base not in SUPPORTED_CURRENCIES or quote not in SUPPORTED_CURRENCIES:
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported currency pair. Supported currencies: {', '.join(SUPPORTED_CURRENCIES)}"
            )
        
        latest_rate = db.query(FxRate)\
            .filter(FxRate.currency_pair == pair)\
            .order_by(FxRate.timestamp.desc())\
            .first()
            
        if not latest_rate:
            raise HTTPException(status_code=404, detail=f"No rate found for pair {pair}")
            
        return {
            "pair": latest_rate.currency_pair,
            "rate": str(latest_rate.rate),
            "timestamp": latest_rate.timestamp
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 