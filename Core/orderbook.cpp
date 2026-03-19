#include "orderbook.h"

OrderBook::OrderBook() {
    bids.resize(MAX_PRICE, 0);
    asks.resize(MAX_PRICE, 0);
    best_bid_idx = 0;
    best_ask_idx = MAX_PRICE - 1;
}

void OrderBook::add_bid(int price_idx, int qty) {
    bids[price_idx] += qty;
    if (price_idx > best_bid_idx) best_bid_idx = price_idx;
}

void OrderBook::add_ask(int price_idx, int qty) {
    asks[price_idx] += qty;
    if (price_idx < best_ask_idx) best_ask_idx = price_idx;
}

int OrderBook::best_bid() const {
    return best_bid_idx;
}

int OrderBook::best_ask() const {
    return best_ask_idx;
}
