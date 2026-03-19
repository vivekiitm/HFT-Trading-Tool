import core

class Strategy:
    def __init__(self):
        self.engine = core.MatchingEngine()

    def on_tick(self, price_idx):
        self.engine.process_order(True, price_idx, 1)
