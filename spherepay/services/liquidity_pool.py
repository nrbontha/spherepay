from decimal import Decimal
from sqlalchemy.orm import Session
from fastapi import HTTPException
from sqlalchemy import func
from datetime import datetime, UTC, timedelta

from ..models.liquidity_pool import LiquidityPool
from ..services.fx_rate import FxRateService
from ..models.transaction import Transaction
from .. import config
from ..logger import logger

class LiquidityPoolService:
    # Rebalancing thresholds
    HIGH_UTILIZATION_THRESHOLD = Decimal('0.7')  # 70%
    LOW_UTILIZATION_THRESHOLD = Decimal('0.3')   # 30%
    REBALANCE_BUFFER_MULTIPLIER = Decimal('1.5') # 50% extra
    METRICS_WINDOW_HOURS = 24                    # Look at last 24h

    def __init__(self, db: Session):
        self.db = db

    def check_liquidity(self, currency: str, amount: Decimal) -> bool:
        """Check if there's enough available liquidity for a transaction"""
        try:
            pool = self.db.query(LiquidityPool)\
                .filter(LiquidityPool.currency == currency)\
                .first()
            
            if not pool:
                logger.error(f"No liquidity pool for {currency}")
                raise HTTPException(
                    status_code=400, 
                    detail=f"No liquidity pool for {currency}"
                )
            
            available = pool.balance - pool.reserved_balance
            if available < amount:
                logger.warning(
                    f"Insufficient liquidity in {currency}. "
                    f"Required: {amount}, Available: {available}"
                )
                
            return available >= amount
            
        except Exception as e:
            logger.error(f"Error checking liquidity: {str(e)}")
            raise

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

    def get_pool_metrics(self, currency: str, hours: int = config.METRICS_WINDOW_HOURS) -> dict:
        """Analyze pool's transaction patterns"""
        since = datetime.now(UTC) - timedelta(hours=hours)
        
        # Get transaction volumes
        outgoing = self.db.query(func.sum(Transaction.source_amount))\
            .filter(Transaction.source_currency == currency)\
            .filter(Transaction.created_at >= since)\
            .scalar() or Decimal('0')
            
        incoming = self.db.query(func.sum(Transaction.target_amount))\
            .filter(Transaction.target_currency == currency)\
            .filter(Transaction.created_at >= since)\
            .scalar() or Decimal('0')
            
        # Get current pool state
        pool = self.db.query(LiquidityPool)\
            .filter(LiquidityPool.currency == currency)\
            .first()
            
        return {
            'currency': currency,
            'current_balance': pool.balance,
            'outgoing_volume': outgoing,
            'incoming_volume': incoming,
            'net_flow': incoming - outgoing,
            'utilization_rate': outgoing / pool.balance if pool.balance > 0 else Decimal('0')
        }

    def internal_rebalance(self, from_currency: str, to_currency: str, amount: Decimal):
        """Execute internal bank transfer between pools"""
        from_pool = self.db.query(LiquidityPool)\
            .filter(LiquidityPool.currency == from_currency)\
            .first()
        to_pool = self.db.query(LiquidityPool)\
            .filter(LiquidityPool.currency == to_currency)\
            .first()

        if not from_pool or not to_pool:
            raise ValueError("Invalid currency pools")

        # Get current FX rate (no margin for internal transfers)
        fx_rate_service = FxRateService(self.db)
        rate = fx_rate_service.get_latest_rate(from_currency, to_currency)
        converted_amount = amount * Decimal(str(rate.rate))

        # Direct balance updates
        from_pool.balance -= amount
        to_pool.balance += converted_amount
        
        self.db.commit()

    def rebalance_pools(self):
        """Analyze and rebalance all pools"""
        # Get all currency pools and their metrics (volume, utilization etc)
        pools = self.db.query(LiquidityPool).all()
        metrics = {p.currency: self.get_pool_metrics(p.currency) for p in pools}
        
        # Check each pool for rebalancing needs
        for currency, metric in metrics.items():
            # Pool needs more liquidity if high utilization or negative net flow
            if (metric['utilization_rate'] > config.REBALANCE_HIGH_UTILIZATION or 
                metric['net_flow'] < 0):
                # Find a pool with excess liquidity to transfer from
                for other_currency, other_metric in metrics.items():
                    if (other_currency != currency and 
                        other_metric['utilization_rate'] < config.REBALANCE_LOW_UTILIZATION):
                        # Transfer net flow amount plus 50% buffer
                        required_amount = abs(metric['net_flow']) * config.REBALANCE_BUFFER_MULTIPLIER
                        self.internal_rebalance(other_currency, currency, required_amount)
                        break  # Only rebalance once per currency