from fastapi import FastAPI, Depends, BackgroundTasks
from sqlalchemy.orm import Session

from .database import get_db
from .schemas.fx_rate import FxRateUpdate
from .schemas.transaction import TransactionRequest
from .services.fx_rate import FxRateService
from .services.transaction import TransactionService

app = FastAPI()

@app.post("/fx-rate")
async def update_fx_rate(
    rate_update: FxRateUpdate, 
    db: Session = Depends(get_db)
):
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

@app.get("/fx-rate/{base}-{quote}")
async def get_latest_rate(
    base: str, 
    quote: str,
    db: Session = Depends(get_db)
):
    fx_service = FxRateService(db)
    latest_rate = fx_service.get_latest_rate(base, quote)
    return {
        "pair": latest_rate.currency_pair,
        "rate": str(latest_rate.rate),
        "timestamp": latest_rate.timestamp
    }

@app.post("/transfer")
async def create_transfer(
    request: TransactionRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    transaction_service = TransactionService(db)
    transaction = transaction_service.create_transaction(request, background_tasks)
    return {
        "status": "success",
        "data": {
            "id": transaction.id,
            "source_currency": transaction.source_currency,
            "target_currency": transaction.target_currency,
            "source_amount": str(transaction.source_amount),
            "target_amount": str(transaction.target_amount),
            "fx_rate": str(transaction.fx_rate),
            "margin": str(transaction.margin),
            "status": transaction.status.value,
            "created_at": transaction.created_at,
            "settled_at": transaction.settled_at
        }
    }

@app.get("/transfer/{transfer_id}")
async def get_transfer(
    transfer_id: int,
    db: Session = Depends(get_db)
):
    transaction_service = TransactionService(db)
    transaction = transaction_service.get_transaction(transfer_id)
    return {
        "status": "success",
        "data": {
            "id": transaction.id,
            "source_currency": transaction.source_currency,
            "target_currency": transaction.target_currency,
            "source_amount": str(transaction.source_amount),
            "target_amount": str(transaction.target_amount),
            "fx_rate": str(transaction.fx_rate),
            "margin": str(transaction.margin),
            "status": transaction.status.value,
            "created_at": transaction.created_at,
            "settled_at": transaction.settled_at
        }
    }
