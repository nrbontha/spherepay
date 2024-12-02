from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas.transaction import TransactionRequest
from ..services.transaction import TransactionService

router = APIRouter()

@router.post("/transfer")
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

@router.get("/transfer/{transfer_id}")
async def get_transfer(transfer_id: int, db: Session = Depends(get_db)):
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