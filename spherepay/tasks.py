from fastapi import BackgroundTasks
import asyncio
from .database import SessionLocal
from .services.liquidity_pool import LiquidityPoolService
from . import config
import logging

logger = logging.getLogger(__name__)

async def rebalance_pools_task():
    """Run pool rebalancing every hour"""
    while True:
        db = SessionLocal()
        try:
            logger.info("Starting scheduled rebalancing")
            liquidity_service = LiquidityPoolService(db)
            liquidity_service.rebalance_pools()
            logger.info("Completed scheduled rebalancing")

        except Exception as e:
            logger.error(f"Error in rebalancing task: {str(e)}")

        finally:
            db.close()

        await asyncio.sleep(config.REBALANCE_INTERVAL_SECONDS)