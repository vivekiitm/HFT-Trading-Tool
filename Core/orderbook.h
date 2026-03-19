#pragma once
#include <vector>
#include <algorithm>

class OrderBook {
public:
    static const int MAX_PRICE = 200000; // price * 1000 (fixed tick)

    std::vector<int> bids;
    std::vector<int> asks;

    int best_bid_idx;
    int best_ask_idx;

    OrderBook();

    void add_bid(int price_idx, int qty);
    void add_ask(int price_idx, int qty);

    int best_bid() const;
    int best_ask() const;
};
