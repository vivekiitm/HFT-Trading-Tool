#include "signal_engine.h"

double SignalEngine::microprice(const OrderBook& ob) {
    int bid = ob.best_bid();
    int ask = ob.best_ask();

    if (bid == 0 || ask == 0) return 0;
    return (bid + ask) / 2.0;
}
