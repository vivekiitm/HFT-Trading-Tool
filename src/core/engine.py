"""
TradingEngine — Coordinates order book, strategy execution, and risk checks.
Designed for minimal overhead per tick.
"""

import asyncio
import time
import uuid
from collections import defaultdict
from typing import Dict, List, Optional

from src.core.order_book import OrderBook
from src.core.risk_manager import RiskManager
from src.core.models import Order, OrderStatus, Trade, Side
from src.strategies.registry import StrategyRegistry
from src.utils.logger import get_logger

logger = get_logger(__name__)


class TradingEngine:
    def __init__(self):
        self.order_books: Dict[str, OrderBook] = {}
        self.risk_manager = RiskManager()
        self.strategy_registry = StrategyRegistry()
        self.orders: Dict[str, Order] = {}
        self.trades: List[Trade] = []
        self._running = False
        self._tick_count = 0
        self._start_time: Optional[float] = None
        self._order_count = 0
        self._fill_count = 0

    async def start(self):
        self._running = True
        self._start_time = time.time()
        # Seed some default symbols
        for symbol in ["AAPL", "TSLA", "MSFT", "NVDA", "BTC-USD"]:
            self.order_books[symbol] = OrderBook(symbol)
        # Start background strategy loop
        asyncio.create_task(self._strategy_loop())
        logger.info(f"Engine started. Symbols: {list(self.order_books.keys())}")

    async def stop(self):
        self._running = False

    async def submit_order(self, order: Order) -> Order:
        """Submit an order through risk checks and into the order book."""
        t0 = time.perf_counter_ns()

        # Risk pre-check
        risk_result = self.risk_manager.check(order)
        if not risk_result.approved:
            order.status = OrderStatus.REJECTED
            order.reject_reason = risk_result.reason
            self.orders[order.order_id] = order
            logger.warning(f"Order {order.order_id} rejected: {risk_result.reason}")
            return order

        # Route to order book
        if order.symbol not in self.order_books:
            self.order_books[order.symbol] = OrderBook(order.symbol)

        book = self.order_books[order.symbol]
        filled_trades = book.add_order(order)

        self.orders[order.order_id] = order
        self.trades.extend(filled_trades)
        self._order_count += 1
        self._fill_count += len(filled_trades)

        latency_us = (time.perf_counter_ns() - t0) / 1_000
        logger.info(
            f"Order {order.order_id} | {order.symbol} {order.side.value} "
            f"{order.quantity}@{order.price} | {order.status.value} | {latency_us:.1f}µs"
        )
        return order

    def cancel_order(self, order_id: str) -> Order:
        order = self.orders.get(order_id)
        if not order:
            raise ValueError(f"Order {order_id} not found")
        if order.status in (OrderStatus.FILLED, OrderStatus.CANCELLED):
            raise ValueError(f"Cannot cancel order in state: {order.status.value}")
        book = self.order_books.get(order.symbol)
        if book:
            book.remove_order(order_id)
        order.status = OrderStatus.CANCELLED
        return order

    def get_order_book_snapshot(self, symbol: str) -> dict:
        book = self.order_books.get(symbol)
        if not book:
            raise ValueError(f"No order book for {symbol}")
        return book.snapshot()

    def get_stats(self) -> dict:
        uptime = time.time() - self._start_time if self._start_time else 0
        return {
            "uptime_seconds": round(uptime, 2),
            "total_orders": self._order_count,
            "total_fills": self._fill_count,
            "fill_rate_pct": round(
                (self._fill_count / self._order_count * 100) if self._order_count else 0, 2
            ),
            "active_symbols": list(self.order_books.keys()),
            "active_strategies": self.strategy_registry.active_strategy_names(),
        }

    async def _strategy_loop(self):
        """Tick strategies every 500ms (simulate HFT signal generation)."""
        while self._running:
            for symbol, book in self.order_books.items():
                snapshot = book.snapshot()
                for strategy in self.strategy_registry.active_strategies():
                    signals = strategy.on_tick(symbol, snapshot)
                    for signal in signals:
                        order = Order(
                            order_id=str(uuid.uuid4()),
                            symbol=signal.symbol,
                            side=signal.side,
                            quantity=signal.quantity,
                            price=signal.price,
                            strategy_id=strategy.strategy_id,
                        )
                        await self.submit_order(order)
            self._tick_count += 1
            await asyncio.sleep(0.5)
