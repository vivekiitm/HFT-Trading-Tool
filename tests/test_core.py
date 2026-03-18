"""
Tests for order book matching, risk manager, and API endpoints.
Run with: pytest tests/ -v
"""

import pytest
import asyncio
import uuid
from src.core.order_book import OrderBook
from src.core.models import Order, Side, OrderStatus
from src.core.risk_manager import RiskManager
from src.core.engine import TradingEngine


# ------------------------------------------------------------------ #
#  Order Book Tests                                                    #
# ------------------------------------------------------------------ #

def make_order(side: Side, price: float, qty: float, symbol: str = "TEST") -> Order:
    return Order(order_id=str(uuid.uuid4()), symbol=symbol, side=side, price=price, quantity=qty)


def test_order_book_no_match():
    book = OrderBook("TEST")
    buy = make_order(Side.BUY, 99.0, 100)
    sell = make_order(Side.SELL, 101.0, 100)
    trades = book.add_order(buy)
    assert trades == []
    trades = book.add_order(sell)
    assert trades == []
    snap = book.snapshot()
    assert snap["best_bid"] == 99.0
    assert snap["best_ask"] == 101.0


def test_order_book_exact_match():
    book = OrderBook("TEST")
    buy = make_order(Side.BUY, 100.0, 100)
    sell = make_order(Side.SELL, 100.0, 100)
    book.add_order(buy)
    trades = book.add_order(sell)
    assert len(trades) == 1
    assert trades[0].quantity == 100.0
    assert trades[0].price == 100.0
    assert buy.status == OrderStatus.FILLED
    assert sell.status == OrderStatus.FILLED


def test_order_book_partial_fill():
    book = OrderBook("TEST")
    buy = make_order(Side.BUY, 100.0, 200)
    sell = make_order(Side.SELL, 100.0, 80)
    book.add_order(buy)
    trades = book.add_order(sell)
    assert len(trades) == 1
    assert trades[0].quantity == 80.0
    assert buy.status == OrderStatus.PARTIALLY_FILLED
    assert sell.status == OrderStatus.FILLED
    assert buy.remaining_quantity() == 120.0


def test_order_book_cancel():
    book = OrderBook("TEST")
    buy = make_order(Side.BUY, 99.0, 100)
    book.add_order(buy)
    removed = book.remove_order(buy.order_id)
    assert removed is not None
    snap = book.snapshot()
    assert snap["best_bid"] is None


def test_order_book_price_priority():
    """Higher bids fill before lower bids."""
    book = OrderBook("TEST")
    book.add_order(make_order(Side.BUY, 100.0, 50))
    book.add_order(make_order(Side.BUY, 101.0, 50))  # better bid
    sell = make_order(Side.SELL, 100.0, 50)
    trades = book.add_order(sell)
    assert trades[0].price == 101.0  # matched against better price


# ------------------------------------------------------------------ #
#  Risk Manager Tests                                                  #
# ------------------------------------------------------------------ #

def test_risk_passes_valid_order():
    rm = RiskManager()
    order = make_order(Side.BUY, 100.0, 100)
    result = rm.check(order)
    assert result.approved


def test_risk_rejects_zero_price():
    rm = RiskManager()
    order = make_order(Side.BUY, 0.0, 100)
    result = rm.check(order)
    assert not result.approved
    assert "Price" in result.reason


def test_risk_rejects_zero_quantity():
    rm = RiskManager()
    order = make_order(Side.BUY, 100.0, 0)
    result = rm.check(order)
    assert not result.approved


def test_risk_rejects_large_notional():
    rm = RiskManager()
    order = make_order(Side.BUY, 100_000.0, 10_000)  # $1B
    result = rm.check(order)
    assert not result.approved
    assert "Notional" in result.reason


# ------------------------------------------------------------------ #
#  Engine Integration Tests                                            #
# ------------------------------------------------------------------ #

@pytest.mark.asyncio
async def test_engine_submit_and_fill():
    engine = TradingEngine()
    await engine.start()

    buy = Order(order_id=str(uuid.uuid4()), symbol="AAPL", side=Side.BUY, price=150.0, quantity=100)
    sell = Order(order_id=str(uuid.uuid4()), symbol="AAPL", side=Side.SELL, price=150.0, quantity=100)

    await engine.submit_order(buy)
    await engine.submit_order(sell)

    assert buy.status == OrderStatus.FILLED
    assert sell.status == OrderStatus.FILLED
    assert len(engine.trades) == 1

    await engine.stop()


@pytest.mark.asyncio
async def test_engine_cancel_order():
    engine = TradingEngine()
    await engine.start()
    order = Order(order_id=str(uuid.uuid4()), symbol="TSLA", side=Side.BUY, price=200.0, quantity=50)
    await engine.submit_order(order)
    cancelled = engine.cancel_order(order.order_id)
    assert cancelled.status == OrderStatus.CANCELLED
    await engine.stop()


@pytest.mark.asyncio
async def test_engine_stats():
    engine = TradingEngine()
    await engine.start()
    stats = engine.get_stats()
    assert "uptime_seconds" in stats
    assert "total_orders" in stats
    await engine.stop()
