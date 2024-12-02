from decimal import Decimal
from sqlalchemy.orm import Session
from fastapi import HTTPException, BackgroundTasks
from datetime import datetime, UTC
import asyncio

from ..models.transaction import Transaction, TransactionStatus
from ..schemas.transaction import TransactionRequest
from .fx_rate import FxRateService
from ..database import SessionLocal
from .liquidity_pool import LiquidityPoolService
from .. import config

class TransactionService:
    def __init__(self, db: Session):
        self.db = db
        self.fx_rate_service = FxRateService(db)
        self.liquidity_pool_service = LiquidityPoolService(db)

    async def process_settlement(self, transaction_id: int):
        db = SessionLocal()
        try:
            transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()
            if not transaction:
                return
            
            liquidity_pool_service = LiquidityPoolService(db)
            
            # Check and reserve funds
            try:
                liquidity_pool_service.reserve_funds(
                    transaction.source_currency, 
                    transaction.source_amount
                )
                transaction.status = TransactionStatus.PROCESSING
                db.commit()
            except HTTPException as e:
                transaction.status = TransactionStatus.FAILED
                db.commit()
                return
            
            # Wait for source currency settlement
            await asyncio.sleep(config.SETTLEMENT_TIMES[transaction.source_currency])
            
            # Wait for target currency settlement
            await asyncio.sleep(config.SETTLEMENT_TIMES[transaction.target_currency])
            
            # Settle the transaction
            try:
                liquidity_pool_service.settle_transaction(
                    transaction.source_currency,
                    transaction.target_currency,
                    transaction.source_amount,
                    transaction.target_amount
                )
                transaction.status = TransactionStatus.COMPLETED
                transaction.settled_at = datetime.now(UTC)
                db.commit()
            except Exception as e:
                transaction.status = TransactionStatus.FAILED
                db.commit()
                raise e
            
        finally:
            db.close()

    def create_transaction(self, request: TransactionRequest, background_tasks: BackgroundTasks) -> Transaction:
        try:
            fx_rate = self.fx_rate_service.get_latest_rate(
                request.source_currency, 
                request.target_currency
            )
            
            source_amount = Decimal(request.source_amount)
            
            # Calculate target amount with margin
            base_target_amount = source_amount * Decimal(str(fx_rate.rate))
            margin_amount = base_target_amount * config.TRANSACTION_MARGIN_RATE
            final_target_amount = base_target_amount - margin_amount
            
            # Create transaction
            transaction = Transaction(
                source_currency=request.source_currency,
                target_currency=request.target_currency,
                source_amount=source_amount,
                target_amount=final_target_amount,
                fx_rate=fx_rate.rate,
                margin=margin_amount,
                revenue=margin_amount,
                status=TransactionStatus.PENDING
            )
            
            self.db.add(transaction)
            self.db.commit()

            # Schedule settlement processing
            background_tasks.add_task(self.process_settlement, transaction.id)
            
            return transaction
            
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=400, detail=str(e))

    def get_transaction(self, transaction_id: int) -> Transaction:
        transaction = self.db.query(Transaction).filter(Transaction.id == transaction_id).first()
        if not transaction:
            raise HTTPException(status_code=404, detail="Transaction not found")
        return transaction