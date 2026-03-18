"""
HFT Trading Tool - Main FastAPI Application
Optimised for low-latency order execution and market data processing.
"""

import time
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.core.order_book import OrderBook
from src.core.engine import TradingEngine
from src.core.risk_manager import RiskManager
from src.api.routes import orders, market_data, strategies, portfolio
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Global engine instance
engine: TradingEngine = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle."""
    global engine
    logger.info("Initialising HFT Trading Engine...")
    engine = TradingEngine()
    await engine.start()
    app.state.engine = engine
    logger.info("Engine started successfully.")
    yield
    logger.info("Shutting down engine...")
    await engine.stop()
    logger.info("Engine stopped.")


app = FastAPI(
    title="HFT Trading Tool",
    description="High-Frequency Trading backend with low-latency APIs",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Latency tracking middleware ---
@app.middleware("http")
async def latency_middleware(request: Request, call_next):
    start = time.perf_counter_ns()
    response = await call_next(request)
    latency_us = (time.perf_counter_ns() - start) / 1_000
    response.headers["X-Latency-Us"] = f"{latency_us:.2f}"
    return response


# --- Include routers ---
app.include_router(orders.router, prefix="/api/v1/orders", tags=["Orders"])
app.include_router(market_data.router, prefix="/api/v1/market", tags=["Market Data"])
app.include_router(strategies.router, prefix="/api/v1/strategies", tags=["Strategies"])
app.include_router(portfolio.router, prefix="/api/v1/portfolio", tags=["Portfolio"])


@app.get("/health", tags=["System"])
async def health_check():
    """Fast health check endpoint."""
    return {"status": "ok", "timestamp_ns": time.time_ns()}


@app.get("/api/v1/stats", tags=["System"])
async def system_stats(request: Request):
    """Engine runtime statistics."""
    eng: TradingEngine = request.app.state.engine
    return eng.get_stats()
