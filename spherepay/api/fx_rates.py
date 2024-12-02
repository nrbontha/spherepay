from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas.fx_rate import FxRateUpdate
from ..services.fx_rate import FxRateService

router = APIRouter()

@router.post("/fx-rate")
async def update_fx_rate(rate_update: FxRateUpdate, db: Session = Depends(get_db)):
    fx_service = FxRateService(db)
    fx_rate = fx_service.create_rate(rate_update)
    return {
        "status": "success",
        "data": {
            "pair": fx_rate.currency_pair,
            "rate": str(fx_rate.rate),
            "timestamp": fx_rate.timestamp
        }
    }

@router.get("/fx-rate/{base}-{quote}")
async def get_latest_rate(base: str, quote: str, db: Session = Depends(get_db)):
    fx_service = FxRateService(db)
    latest_rate = fx_service.get_latest_rate(base, quote)
    return {
        "pair": latest_rate.currency_pair,
        "rate": str(latest_rate.rate),
        "timestamp": latest_rate.timestamp
    } 