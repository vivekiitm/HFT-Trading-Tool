#include "matching_engine.h"

void MatchingEngine::process_order(bool is_buy, int price_idx, int qty) {
    if (is_buy) {
        ob.add_bid(price_idx, qty);
    } else {
        ob.add_ask(price_idx, qty);
    }
}
