"""Market Data API — order book snapshots, trades, OHLCV simulation."""

import time
import random
from fastapi import APIRouter, HTTPException, Request
from typing import List

from src.core.engine import TradingEngine

router = APIRouter()


@router.get("/orderbook/{symbol}", summary="Get order book snapshot")
async def get_order_book(symbol: str, request: Request):
    engine: TradingEngine = request.app.state.engine
    try:
        return engine.get_order_book_snapshot(symbol.upper())
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/trades", summary="Get recent trades (latest 50)")
async def get_trades(request: Request, symbol: str = None, limit: int = 50):
    engine: TradingEngine = request.app.state.engine
    trades = engine.trades
    if symbol:
        trades = [t for t in trades if t.symbol == symbol.upper()]
    trades = sorted(trades, key=lambda t: t.timestamp_ns, reverse=True)
    return [t.to_dict() for t in trades[:limit]]


@router.get("/symbols", summary="List active symbols")
async def list_symbols(request: Request):
    engine: TradingEngine = request.app.state.engine
    return {"symbols": list(engine.order_books.keys())}


@router.get("/ticker/{symbol}", summary="Quick ticker: best bid/ask/last")
async def get_ticker(symbol: str, request: Request):
    engine: TradingEngine = request.app.state.engine
    sym = symbol.upper()
    book = engine.order_books.get(sym)
    if not book:
        raise HTTPException(status_code=404, detail=f"No data for {sym}")
    snap = book.snapshot()
    return {
        "symbol": sym,
        "best_bid": snap["best_bid"],
        "best_ask": snap["best_ask"],
        "spread": snap["spread"],
        "last_trade_price": snap["last_trade_price"],
        "timestamp_ns": snap["timestamp_ns"],
    }


@router.post("/seed/{symbol}", summary="Seed order book with simulated liquidity")
async def seed_order_book(symbol: str, request: Request, mid_price: float = 100.0, levels: int = 5):
    """
    Utility endpoint: populates an order book with realistic-looking
    bid/ask ladders around a given mid price. Useful for testing strategies.
    """
    import uuid
    from src.core.models import Order, Side

    engine: TradingEngine = request.app.state.engine
    sym = symbol.upper()

    seeded = []
    tick = mid_price * 0.001  # 10bps tick

    for i in range(1, levels + 1):
        # Bids below mid
        bid_order = Order(
            order_id=str(uuid.uuid4()),
            symbol=sym,
            side=Side.BUY,
            quantity=round(random.uniform(50, 500), 0),
            price=round(mid_price - tick * i, 4),
            strategy_id="seed",
        )
        await engine.submit_order(bid_order)
        seeded.append(bid_order.to_dict())

        # Asks above mid
        ask_order = Order(
            order_id=str(uuid.uuid4()),
            symbol=sym,
            side=Side.SELL,
            quantity=round(random.uniform(50, 500), 0),
            price=round(mid_price + tick * i, 4),
            strategy_id="seed",
        )
        await engine.submit_order(ask_order)
        seeded.append(ask_order.to_dict())

    return {"seeded": len(seeded), "symbol": sym, "mid_price": mid_price}
