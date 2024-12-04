from decimal import Decimal
from sqlalchemy.orm import Session
from fastapi import HTTPException
from sqlalchemy import func
from datetime import datetime, UTC, timedelta

from .. import config
from ..logger import logger
from ..models.liquidity_pool import LiquidityPool
from ..models.transaction import Transaction
from ..services.fx_rate import FxRateService


class LiquidityPoolService:
    def __init__(self, db: Session):
        self.db = db

    def reserve_funds(self, currency: str, amount: Decimal):
        """Reserve funds for a pending transaction"""
        try:
            pool = self.db.query(LiquidityPool)\
                .filter(LiquidityPool.currency == currency)\
                .first()
            
            if not pool:
                logger.error(f"No liquidity pool found for {currency}")
                raise HTTPException(status_code=400, detail=f"No liquidity pool for {currency}")
            
            available = pool.balance - pool.reserved_balance
            if available < amount:
                logger.error(f"Insufficient liquidity in {currency}. Required: {amount}, Available: {available}")
                raise HTTPException(status_code=400, detail=f"Insufficient liquidity in {currency}")
            
            pool.reserved_balance += amount
            self.db.commit()
            logger.info(f"Reserved {amount} {currency}")
            
        except Exception as e:
            logger.error(f"Error reserving funds: {str(e)}")
            self.db.rollback()
            raise

    def settle_transaction(self, source_currency: str, target_currency: str, 
                         source_amount: Decimal, target_amount: Decimal):
        """Update balances after transaction settlement"""
        try:
            source_pool = self.db.query(LiquidityPool)\
                .filter(LiquidityPool.currency == source_currency)\
                .first()
            target_pool = self.db.query(LiquidityPool)\
                .filter(LiquidityPool.currency == target_currency)\
                .first()
            
            if not source_pool or not target_pool:
                logger.error("Invalid currency pools")
                raise HTTPException(status_code=400, detail="Invalid currency pools")
            
            # Release reserved amount and deduct from target pool
            target_pool.reserved_balance -= target_amount
            target_pool.balance -= target_amount
            
            # Add to source pool
            source_pool.balance += source_amount
            
            self.db.commit()
            logger.info(
                f"Settled transaction: {source_amount} {source_currency} -> "
                f"{target_amount} {target_currency}"
            )
            
        except Exception as e:
            logger.error(f"Error settling transaction: {str(e)}")
            self.db.rollback()
            raise

    def get_pool_metrics(self, currency: str, hours: int = config.METRICS_WINDOW_HOURS) -> dict:
        """Analyze pool's transaction patterns"""
        since = datetime.now(UTC) - timedelta(hours=hours)
        
        # Get transaction volumes
        outgoing = self.db.query(func.sum(Transaction.target_amount))\
            .filter(Transaction.target_currency == currency)\
            .filter(Transaction.created_at >= since)\
            .scalar() or Decimal('0')
            
        incoming = self.db.query(func.sum(Transaction.source_amount))\
            .filter(Transaction.source_currency == currency)\
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
        try:
            from_pool = self.db.query(LiquidityPool)\
                .filter(LiquidityPool.currency == from_currency)\
                .first()
            to_pool = self.db.query(LiquidityPool)\
                .filter(LiquidityPool.currency == to_currency)\
                .first()

            if not from_pool or not to_pool:
                logger.error(f"Invalid currency pools: {from_currency}, {to_currency}")
                raise ValueError("Invalid currency pools")

            # Check if source pool has sufficient balance
            if from_pool.balance < amount:
                logger.warning(f"Insufficient balance in {from_currency} pool for rebalance")
                return

            # Get current FX rate
            fx_rate_service = FxRateService(self.db)
            rate = fx_rate_service.get_latest_rate(from_currency, to_currency)
            converted_amount = amount * Decimal(str(rate.rate))

            # Direct balance updates
            from_pool.balance -= amount
            to_pool.balance += converted_amount
            
            self.db.commit()
            logger.info(
                f"Internal rebalance: {amount} {from_currency} -> "
                f"{converted_amount} {to_currency}"
            )
            
        except Exception as e:
            logger.error(f"Error during internal rebalance: {str(e)}")
            self.db.rollback()
            raise

    def rebalance_pools(self):
        """Analyze and rebalance all pools"""
        pools = self.db.query(LiquidityPool).all()
        metrics = {p.currency: self.get_pool_metrics(p.currency) for p in pools}
        fx_service = FxRateService(self.db)
        
        for currency, metric in metrics.items():
            if (metric['utilization_rate'] > config.REBALANCE_HIGH_UTILIZATION or 
                metric['net_flow'] < 0):
                for other_currency, other_metric in metrics.items():
                    if (other_currency != currency and 
                        other_metric['utilization_rate'] < config.REBALANCE_LOW_UTILIZATION):
                        # Calculate required amount in target currency
                        target_required = abs(metric['net_flow']) * config.REBALANCE_BUFFER_MULTIPLIER
                        
                        # Convert to source currency
                        rate = fx_service.get_latest_rate(currency, other_currency)
                        source_required = target_required * Decimal(str(rate.rate))
                        
                        source_pool = self.db.query(LiquidityPool)\
                            .filter(LiquidityPool.currency == other_currency)\
                            .first()
                        
                        # Don't transfer more than 50% of source pool
                        transfer_amount = min(
                            source_required,
                            source_pool.balance * Decimal('0.5')
                        )
                        
                        if transfer_amount > 0:
                            self.internal_rebalance(other_currency, currency, transfer_amount)
                        break