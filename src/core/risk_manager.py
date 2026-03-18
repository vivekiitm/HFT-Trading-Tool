"""
RiskManager — Pre-trade risk checks before order hits the book.
All checks run in O(1) time.
"""

from dataclasses import dataclass
from typing import Optional
from src.core.models import Order, Side
from src.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class RiskResult:
    approved: bool
    reason: Optional[str] = None


class RiskManager:
    def __init__(self):
        # Configurable limits
        self.max_order_quantity = 10_000
        self.max_order_value = 5_000_000.0   # $5M per order
        self.max_price = 1_000_000.0
        self.min_price = 0.0001
        self.allowed_symbols: Optional[set] = None  # None = all allowed
        self._rejected_count = 0
        self._approved_count = 0

    def check(self, order: Order) -> RiskResult:
        """Run all pre-trade checks. Returns first failure."""
        checks = [
            self._check_price,
            self._check_quantity,
            self._check_notional,
            self._check_symbol,
        ]
        for check in checks:
            result = check(order)
            if not result.approved:
                self._rejected_count += 1
                return result

        self._approved_count += 1
        return RiskResult(approved=True)

    def _check_price(self, order: Order) -> RiskResult:
        if order.price < self.min_price:
            return RiskResult(False, f"Price {order.price} below minimum {self.min_price}")
        if order.price > self.max_price:
            return RiskResult(False, f"Price {order.price} exceeds max {self.max_price}")
        return RiskResult(True)

    def _check_quantity(self, order: Order) -> RiskResult:
        if order.quantity <= 0:
            return RiskResult(False, "Quantity must be positive")
        if order.quantity > self.max_order_quantity:
            return RiskResult(False, f"Quantity {order.quantity} exceeds max {self.max_order_quantity}")
        return RiskResult(True)

    def _check_notional(self, order: Order) -> RiskResult:
        notional = order.quantity * order.price
        if notional > self.max_order_value:
            return RiskResult(False, f"Notional {notional:,.0f} exceeds max {self.max_order_value:,.0f}")
        return RiskResult(True)

    def _check_symbol(self, order: Order) -> RiskResult:
        if self.allowed_symbols and order.symbol not in self.allowed_symbols:
            return RiskResult(False, f"Symbol {order.symbol} not in allowed list")
        return RiskResult(True)

    def stats(self) -> dict:
        total = self._approved_count + self._rejected_count
        return {
            "approved": self._approved_count,
            "rejected": self._rejected_count,
            "rejection_rate_pct": round(self._rejected_count / total * 100, 2) if total else 0,
        }
