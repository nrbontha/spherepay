from decimal import Decimal
from sqlalchemy.orm import Session
from fastapi import HTTPException

from ..models.liquidity_pool import LiquidityPool

class LiquidityPoolService:
    def __init__(self, db: Session):
        self.db = db

    def check_liquidity(self, currency: str, amount: Decimal) -> bool:
        """Check if there's enough available liquidity for a transaction"""
        pool = self.db.query(LiquidityPool)\
            .filter(LiquidityPool.currency == currency)\
            .first()
        
        if not pool:
            raise HTTPException(status_code=400, detail=f"No liquidity pool for {currency}")
        
        available = pool.balance - pool.reserved_balance
        return available >= amount

    def reserve_funds(self, currency: str, amount: Decimal):
        """Reserve funds for a pending transaction"""
        pool = self.db.query(LiquidityPool)\
            .filter(LiquidityPool.currency == currency)\
            .first()
        
        if not pool:
            raise HTTPException(status_code=400, detail=f"No liquidity pool for {currency}")
        
        available = pool.balance - pool.reserved_balance
        if available < amount:
            raise HTTPException(status_code=400, detail=f"Insufficient liquidity in {currency}")
        
        pool.reserved_balance += amount
        self.db.commit()

    def settle_transaction(self, source_currency: str, target_currency: str, 
                         source_amount: Decimal, target_amount: Decimal):
        """Update balances after transaction settlement"""
        source_pool = self.db.query(LiquidityPool)\
            .filter(LiquidityPool.currency == source_currency)\
            .first()
        target_pool = self.db.query(LiquidityPool)\
            .filter(LiquidityPool.currency == target_currency)\
            .first()
        
        if not source_pool or not target_pool:
            raise HTTPException(status_code=400, detail="Invalid currency pools")
        
        # Release reserved amount and deduct from source pool
        source_pool.reserved_balance -= source_amount
        source_pool.balance -= source_amount
        
        # Add to target pool
        target_pool.balance += target_amount
        
        self.db.commit() 