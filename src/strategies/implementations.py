"""
Concrete HFT strategies:
  1. MarketMaker  — posts bid/ask around mid-price
  2. MomentumScalper — trades in direction of spread compression
  3. MeanReversion — fades large spread widenings
"""

import random
from typing import List
from src.strategies.base import BaseStrategy, Signal
from src.core.models import Side


class MarketMakerStrategy(BaseStrategy):
    """
    Simple market-making strategy.
    Posts a bid below mid and an ask above mid by a configurable edge.
    """

    def __init__(self, edge_bps: float = 5.0, quantity: float = 100.0):
        super().__init__("market_maker", "Market Maker")
        self.edge_bps = edge_bps  # half-spread in basis points
        self.quantity = quantity

    def on_tick(self, symbol: str, snapshot: dict) -> List[Signal]:
        if not self.enabled:
            return []
        mid = snapshot.get("mid_price")
        if not mid:
            return []

        edge = mid * (self.edge_bps / 10_000)
        bid_price = round(mid - edge, 4)
        ask_price = round(mid + edge, 4)

        self.signal_count += 2
        return [
            Signal(symbol=symbol, side=Side.BUY, price=bid_price, quantity=self.quantity),
            Signal(symbol=symbol, side=Side.SELL, price=ask_price, quantity=self.quantity),
        ]


class MomentumScalperStrategy(BaseStrategy):
    """
    Momentum scalper — follows best bid/ask movement.
    Buys when spread is tight (liquidity signal), sells when it widens.
    """

    def __init__(self, max_spread_bps: float = 10.0, quantity: float = 50.0):
        super().__init__("momentum_scalper", "Momentum Scalper")
        self.max_spread_bps = max_spread_bps
        self.quantity = quantity
        self._prev_mid: float = 0.0

    def on_tick(self, symbol: str, snapshot: dict) -> List[Signal]:
        if not self.enabled:
            return []

        best_bid = snapshot.get("best_bid")
        best_ask = snapshot.get("best_ask")
        mid = snapshot.get("mid_price")

        if not (best_bid and best_ask and mid):
            return []

        spread_bps = (best_ask - best_bid) / mid * 10_000

        signals = []
        if spread_bps <= self.max_spread_bps:
            if mid > self._prev_mid and self._prev_mid > 0:
                # Price moving up — buy at ask
                signals.append(Signal(symbol=symbol, side=Side.BUY, price=best_ask, quantity=self.quantity))
            elif mid < self._prev_mid and self._prev_mid > 0:
                # Price moving down — sell at bid
                signals.append(Signal(symbol=symbol, side=Side.SELL, price=best_bid, quantity=self.quantity))

        self._prev_mid = mid
        self.signal_count += len(signals)
        return signals


class MeanReversionStrategy(BaseStrategy):
    """
    Mean reversion — fades extreme spread widenings.
    Assumes spread will revert; places limit orders at current best prices.
    """

    def __init__(self, trigger_spread_bps: float = 20.0, quantity: float = 75.0):
        super().__init__("mean_reversion", "Mean Reversion")
        self.trigger_spread_bps = trigger_spread_bps
        self.quantity = quantity

    def on_tick(self, symbol: str, snapshot: dict) -> List[Signal]:
        if not self.enabled:
            return []

        best_bid = snapshot.get("best_bid")
        best_ask = snapshot.get("best_ask")
        mid = snapshot.get("mid_price")

        if not (best_bid and best_ask and mid):
            return []

        spread_bps = (best_ask - best_bid) / mid * 10_000

        if spread_bps < self.trigger_spread_bps:
            return []

        # Spread is wide — fade by posting inside the spread
        inside_bid = round(best_bid + (best_ask - best_bid) * 0.25, 4)
        inside_ask = round(best_ask - (best_ask - best_bid) * 0.25, 4)

        self.signal_count += 2
        return [
            Signal(symbol=symbol, side=Side.BUY, price=inside_bid, quantity=self.quantity),
            Signal(symbol=symbol, side=Side.SELL, price=inside_ask, quantity=self.quantity),
        ]
