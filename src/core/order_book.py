"""
OrderBook — Price-time priority matching engine using sorted dicts.
Optimised for O(log n) insertion and O(1) best bid/ask lookup.
"""

import time
from sortedcontainers import SortedDict
from typing import Dict, List, Optional
from src.core.models import Order, OrderStatus, Trade, Side, PriceLevel


class OrderBook:
    def __init__(self, symbol: str):
        self.symbol = symbol
        # bids: highest price first (use negative key trick)
        self._bids: SortedDict = SortedDict(lambda x: -x)
        # asks: lowest price first
        self._asks: SortedDict = SortedDict()
        # Fast lookup by order_id
        self._order_map: Dict[str, Order] = {}
        self._last_trade_price: Optional[float] = None
        self._trade_count = 0

    # ------------------------------------------------------------------ #
    #  Public API                                                          #
    # ------------------------------------------------------------------ #

    def add_order(self, order: Order) -> List[Trade]:
        """Add order and immediately attempt matching. Returns filled trades."""
        order.status = OrderStatus.OPEN
        self._order_map[order.order_id] = order

        trades: List[Trade] = []

        if order.side == Side.BUY:
            trades = self._match_buy(order)
        else:
            trades = self._match_sell(order)

        # If not fully filled, rest on book
        if order.remaining_quantity() > 1e-9:
            self._add_to_book(order)
        elif order.status != OrderStatus.FILLED:
            order.status = OrderStatus.FILLED

        return trades

    def remove_order(self, order_id: str) -> Optional[Order]:
        """Remove a resting order by ID."""
        order = self._order_map.get(order_id)
        if not order:
            return None
        side_book = self._bids if order.side == Side.BUY else self._asks
        level = side_book.get(order.price)
        if level:
            level[:] = [o for o in level if o.order_id != order_id]
            if not level:
                del side_book[order.price]
        del self._order_map[order_id]
        return order

    def snapshot(self) -> dict:
        """Return top-of-book + depth snapshot."""
        bids = [
            {"price": p, "quantity": sum(o.remaining_quantity() for o in orders), "orders": len(orders)}
            for p, orders in list(self._bids.items())[:10]
        ]
        asks = [
            {"price": p, "quantity": sum(o.remaining_quantity() for o in orders), "orders": len(orders)}
            for p, orders in list(self._asks.items())[:10]
        ]
        best_bid = bids[0]["price"] if bids else None
        best_ask = asks[0]["price"] if asks else None
        spread = round(best_ask - best_bid, 4) if (best_bid and best_ask) else None

        return {
            "symbol": self.symbol,
            "best_bid": best_bid,
            "best_ask": best_ask,
            "spread": spread,
            "mid_price": round((best_bid + best_ask) / 2, 4) if (best_bid and best_ask) else None,
            "last_trade_price": self._last_trade_price,
            "total_trades": self._trade_count,
            "bids": bids,
            "asks": asks,
            "timestamp_ns": time.time_ns(),
        }

    def best_bid(self) -> Optional[float]:
        return next(iter(self._bids), None)

    def best_ask(self) -> Optional[float]:
        return next(iter(self._asks), None)

    # ------------------------------------------------------------------ #
    #  Internal matching                                                   #
    # ------------------------------------------------------------------ #

    def _match_buy(self, order: Order) -> List[Trade]:
        trades = []
        while order.remaining_quantity() > 1e-9 and self._asks:
            best_ask_price = next(iter(self._asks))
            if order.price < best_ask_price:
                break
            trades.extend(self._fill_against(order, self._asks, best_ask_price, Side.SELL))
        return trades

    def _match_sell(self, order: Order) -> List[Trade]:
        trades = []
        while order.remaining_quantity() > 1e-9 and self._bids:
            best_bid_price = next(iter(self._bids))
            if order.price > best_bid_price:
                break
            trades.extend(self._fill_against(order, self._bids, best_bid_price, Side.BUY))
        return trades

    def _fill_against(self, aggressor: Order, book: SortedDict, price: float, resting_side: Side) -> List[Trade]:
        trades = []
        level = book.get(price, [])
        remaining_level = []

        for resting in level:
            if aggressor.remaining_quantity() <= 1e-9:
                remaining_level.append(resting)
                continue

            fill_qty = min(aggressor.remaining_quantity(), resting.remaining_quantity())
            fill_price = resting.price

            # Update both orders
            aggressor.filled_quantity += fill_qty
            resting.filled_quantity += fill_qty
            aggressor.avg_fill_price = self._update_avg(aggressor, fill_qty, fill_price)
            resting.avg_fill_price = self._update_avg(resting, fill_qty, fill_price)

            if resting.remaining_quantity() <= 1e-9:
                resting.status = OrderStatus.FILLED
            else:
                resting.status = OrderStatus.PARTIALLY_FILLED
                remaining_level.append(resting)

            if aggressor.remaining_quantity() <= 1e-9:
                aggressor.status = OrderStatus.FILLED
            else:
                aggressor.status = OrderStatus.PARTIALLY_FILLED

            trade = Trade(
                symbol=aggressor.symbol,
                buy_order_id=aggressor.order_id if aggressor.side == Side.BUY else resting.order_id,
                sell_order_id=resting.order_id if resting.side == Side.SELL else aggressor.order_id,
                quantity=fill_qty,
                price=fill_price,
            )
            trades.append(trade)
            self._last_trade_price = fill_price
            self._trade_count += 1

        if remaining_level:
            book[price] = remaining_level
        else:
            del book[price]

        return trades

    def _add_to_book(self, order: Order):
        book = self._bids if order.side == Side.BUY else self._asks
        if order.price not in book:
            book[order.price] = []
        book[order.price].append(order)

    @staticmethod
    def _update_avg(order: Order, fill_qty: float, fill_price: float) -> float:
        prev_value = order.avg_fill_price * (order.filled_quantity - fill_qty)
        return (prev_value + fill_qty * fill_price) / order.filled_quantity
