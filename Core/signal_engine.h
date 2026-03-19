#pragma once
#include "orderbook.h"

class SignalEngine {
public:
    static double microprice(const OrderBook& ob);
};
