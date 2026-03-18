"""Strategy registry — manages all strategy instances."""

from typing import Dict, List
from src.strategies.base import BaseStrategy
from src.strategies.implementations import (
    MarketMakerStrategy,
    MomentumScalperStrategy,
    MeanReversionStrategy,
)


class StrategyRegistry:
    def __init__(self):
        self._strategies: Dict[str, BaseStrategy] = {}
        self._register_defaults()

    def _register_defaults(self):
        for s in [MarketMakerStrategy(), MomentumScalperStrategy(), MeanReversionStrategy()]:
            self._strategies[s.strategy_id] = s

    def get(self, strategy_id: str) -> BaseStrategy:
        if strategy_id not in self._strategies:
            raise ValueError(f"Strategy '{strategy_id}' not found")
        return self._strategies[strategy_id]

    def all_strategies(self) -> List[BaseStrategy]:
        return list(self._strategies.values())

    def active_strategies(self) -> List[BaseStrategy]:
        return [s for s in self._strategies.values() if s.enabled]

    def active_strategy_names(self) -> List[str]:
        return [s.name for s in self.active_strategies()]

    def enable(self, strategy_id: str):
        self.get(strategy_id).enable()

    def disable(self, strategy_id: str):
        self.get(strategy_id).disable()
