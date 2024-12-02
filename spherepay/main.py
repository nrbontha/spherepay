from fastapi import FastAPI
from contextlib import asynccontextmanager
import asyncio

from .tasks import rebalance_pools_task
from .api import fx_rates, transfers


@asynccontextmanager
async def lifespan(app: FastAPI):
    rebalance_task = asyncio.create_task(rebalance_pools_task())
    yield
    rebalance_task.cancel()

app = FastAPI(lifespan=lifespan)

# Include routers
app.include_router(fx_rates.router)
app.include_router(transfers.router)
