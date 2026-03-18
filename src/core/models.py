"""
Core domain models for the HFT trading system.
Uses Python dataclasses for zero-overhead instantiation.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
import time
import uuid


class Side(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


class OrderType(str, Enum):
    LIMIT = "LIMIT"
    MARKET = "MARKET"


class OrderStatus(str, Enum):
    PENDING = "PENDING"
    OPEN = "OPEN"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    FILLED = "FILLED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"


@dataclass
class Order:
    symbol: str
    side: Side
    quantity: float
    price: float  # 0.0 for MARKET orders
    order_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    order_type: OrderType = OrderType.LIMIT
    status: OrderStatus = OrderStatus.PENDING
    filled_quantity: float = 0.0
    avg_fill_price: float = 0.0
    timestamp_ns: int = field(default_factory=time.time_ns)
    strategy_id: Optional[str] = None
    reject_reason: Optional[str] = None

    def remaining_quantity(self) -> float:
        return self.quantity - self.filled_quantity

    def to_dict(self) -> dict:
        return {
            "order_id": self.order_id,
            "symbol": self.symbol,
            "side": self.side.value,
            "order_type": self.order_type.value,
            "quantity": self.quantity,
            "price": self.price,
            "status": self.status.value,
            "filled_quantity": self.filled_quantity,
            "avg_fill_price": self.avg_fill_price,
            "timestamp_ns": self.timestamp_ns,
            "strategy_id": self.strategy_id,
            "reject_reason": self.reject_reason,
        }


@dataclass
class Trade:
    trade_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    symbol: str = ""
    buy_order_id: str = ""
    sell_order_id: str = ""
    quantity: float = 0.0
    price: float = 0.0
    timestamp_ns: int = field(default_factory=time.time_ns)

    def to_dict(self) -> dict:
        return {
            "trade_id": self.trade_id,
            "symbol": self.symbol,
            "buy_order_id": self.buy_order_id,
            "sell_order_id": self.sell_order_id,
            "quantity": self.quantity,
            "price": self.price,
            "timestamp_ns": self.timestamp_ns,
        }


@dataclass
class PriceLevel:
    price: float
    total_quantity: float = 0.0
    order_count: int = 0
