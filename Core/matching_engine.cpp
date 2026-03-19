#pragma once
#include "orderbook.h"

class MatchingEngine {
public:
    OrderBook ob;

    void process_order(bool is_buy, double price, int qty);
};
