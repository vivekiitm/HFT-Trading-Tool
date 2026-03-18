"""
Strategy base class and registry.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional
from src.core.models import Side


@dataclass
class Signal:
    symbol: str
    side: Side
    price: float
    quantity: float


class BaseStrategy(ABC):
    def __init__(self, strategy_id: str, name: str):
        self.strategy_id = strategy_id
        self.name = name
        self.enabled = False
        self.signal_count = 0

    @abstractmethod
    def on_tick(self, symbol: str, snapshot: dict) -> List[Signal]:
        pass

    def enable(self):
        self.enabled = True

    def disable(self):
        self.enabled = False

    def to_dict(self) -> dict:
        return {
            "strategy_id": self.strategy_id,
            "name": self.name,
            "enabled": self.enabled,
            "signal_count": self.signal_count,
        }
