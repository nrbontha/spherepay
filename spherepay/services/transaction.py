from decimal import Decimal
from sqlalchemy.orm import Session
from fastapi import HTTPException, BackgroundTasks
from datetime import datetime, UTC
import asyncio

from .. import config
from .fx_rate import FxRateService
from .liquidity_pool import LiquidityPoolService
from ..database import SessionLocal
from ..models.transaction import Transaction, TransactionStatus
from ..schemas.transaction import TransactionRequest
from ..logger import logger


class TransactionService:
    def __init__(self, db: Session):
        self.db = db

    async def process_settlement(self, transaction_id: int):
        db = SessionLocal()
        try:
            transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()
            if not transaction:
                logger.error(f"Transaction {transaction_id} not found")
                return
                
            logger.info(f"Processing settlement for transaction {transaction_id}")
            
            # Reserve funds
            try:
                liquidity_service = LiquidityPoolService(db)
                liquidity_service.reserve_funds(
                    transaction.target_currency, 
                    transaction.target_amount
                )
                transaction.status = TransactionStatus.PROCESSING
                db.commit()
                logger.info(f"Reserved funds for transaction {transaction_id}")
            except HTTPException as e:
                logger.error(f"Failed to reserve funds: {str(e)}")
                transaction.status = TransactionStatus.FAILED
                db.commit()
                return
                
            # Settlement
            logger.info(f"Starting settlement delay for transaction {transaction_id}")
            await asyncio.sleep(config.SETTLEMENT_TIMES[transaction.source_currency])
            await asyncio.sleep(config.SETTLEMENT_TIMES[transaction.target_currency])
            
            try:
                liquidity_service.settle_transaction(
                    transaction.source_currency,
                    transaction.target_currency,
                    transaction.source_amount,
                    transaction.target_amount
                )
                transaction.status = TransactionStatus.COMPLETED
                transaction.settled_at = datetime.now(UTC)
                db.commit()
                logger.info(f"Settlement completed for transaction {transaction_id}")
            except Exception as e:
                logger.error(f"Settlement failed: {str(e)}")
                transaction.status = TransactionStatus.FAILED
                db.commit()
                raise
                
        finally:
            db.close()

    def create_transaction(self, request: TransactionRequest, background_tasks: BackgroundTasks) -> Transaction:
        try:
            logger.info(
                f"New transfer request: {request.source_currency}->{request.target_currency} "
                f"Amount: {request.source_amount}"
            )
            
            # Use local instance of FxRateService
            fx_rate_service = FxRateService(self.db)
            fx_rate = fx_rate_service.get_latest_rate(
                request.source_currency, 
                request.target_currency
            )
            
            source_amount = Decimal(request.source_amount)

            # Calculate target amount with margin
            base_target_amount = source_amount * Decimal(str(fx_rate.rate))
            margin = config.TRANSACTION_MARGIN_RATE
            margin_amount = base_target_amount * margin
            final_target_amount = base_target_amount - margin_amount

            # Create transaction
            transaction = Transaction(
                source_currency=request.source_currency,
                target_currency=request.target_currency,
                source_amount=source_amount,
                target_amount=final_target_amount,
                fx_rate=fx_rate.rate,
                margin=margin,
                revenue=margin_amount,
                status=TransactionStatus.PENDING
            )
            
            self.db.add(transaction)
            self.db.commit()

            logger.info(f"Created transaction {transaction.id}")

            # Schedule settlement processing
            background_tasks.add_task(self.process_settlement, transaction.id)
            
            return transaction
            
        except Exception as e:
            logger.error(f"Failed to create transaction: {str(e)}")
            self.db.rollback()
            raise HTTPException(status_code=400, detail=str(e))

    def get_transaction(self, transaction_id: int) -> Transaction:
        transaction = self.db.query(Transaction).filter(Transaction.id == transaction_id).first()
        if not transaction:
            raise HTTPException(status_code=404, detail="Transaction not found")
        return transaction