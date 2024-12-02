from fastapi import BackgroundTasks
import asyncio
from .database import SessionLocal
from .services.liquidity_pool import LiquidityPoolService
from . import config

async def rebalance_pools_task():
    """Run pool rebalancing every hour"""
    while True:
        db = SessionLocal()
        try:
            liquidity_service = LiquidityPoolService(db)
            liquidity_service.rebalance_pools()
        finally:
            db.close()
        await asyncio.sleep(config.REBALANCE_INTERVAL_SECONDS)