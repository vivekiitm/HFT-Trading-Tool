"""Portfolio API — PnL, positions, risk stats."""

from fastapi import APIRouter, Request
from collections import defaultdict
from src.core.engine import TradingEngine
from src.core.models import Side

router = APIRouter()


@router.get("/positions", summary="Get current net positions per symbol")
async def get_positions(request: Request):
    engine: TradingEngine = request.app.state.engine
    positions: dict = defaultdict(float)
    cost_basis: dict = defaultdict(float)

    for order in engine.orders.values():
        if order.filled_quantity <= 0:
            continue
        sign = 1.0 if order.side == Side.BUY else -1.0
        positions[order.symbol] += sign * order.filled_quantity
        cost_basis[order.symbol] += sign * order.filled_quantity * order.avg_fill_price

    result = []
    for symbol, qty in positions.items():
        book = engine.order_books.get(symbol)
        last_price = book.snapshot().get("last_trade_price") if book else None
        avg_price = abs(cost_basis[symbol] / qty) if qty != 0 else 0
        unrealised_pnl = (last_price - avg_price) * qty if last_price and qty != 0 else None
        result.append({
            "symbol": symbol,
            "net_quantity": round(qty, 4),
            "avg_price": round(avg_price, 4),
            "last_price": last_price,
            "unrealised_pnl": round(unrealised_pnl, 2) if unrealised_pnl is not None else None,
        })

    return sorted(result, key=lambda x: abs(x["net_quantity"]), reverse=True)


@router.get("/pnl", summary="Aggregate realised PnL across all trades")
async def get_pnl(request: Request):
    engine: TradingEngine = request.app.state.engine
    # Simple approach: sum up fill values by side
    buy_value: dict = defaultdict(float)
    sell_value: dict = defaultdict(float)
    buy_qty: dict = defaultdict(float)
    sell_qty: dict = defaultdict(float)

    for order in engine.orders.values():
        if order.filled_quantity <= 0:
            continue
        sym = order.symbol
        if order.side == Side.BUY:
            buy_value[sym] += order.filled_quantity * order.avg_fill_price
            buy_qty[sym] += order.filled_quantity
        else:
            sell_value[sym] += order.filled_quantity * order.avg_fill_price
            sell_qty[sym] += order.filled_quantity

    symbols = set(list(buy_value.keys()) + list(sell_value.keys()))
    pnl_breakdown = []
    total_pnl = 0.0

    for sym in symbols:
        matched_qty = min(buy_qty[sym], sell_qty[sym])
        if matched_qty <= 0:
            continue
        avg_buy = buy_value[sym] / buy_qty[sym] if buy_qty[sym] else 0
        avg_sell = sell_value[sym] / sell_qty[sym] if sell_qty[sym] else 0
        realised = (avg_sell - avg_buy) * matched_qty
        total_pnl += realised
        pnl_breakdown.append({
            "symbol": sym,
            "matched_qty": round(matched_qty, 4),
            "avg_buy_price": round(avg_buy, 4),
            "avg_sell_price": round(avg_sell, 4),
            "realised_pnl": round(realised, 2),
        })

    return {
        "total_realised_pnl": round(total_pnl, 2),
        "breakdown": sorted(pnl_breakdown, key=lambda x: abs(x["realised_pnl"]), reverse=True),
    }


@router.get("/risk", summary="Current risk manager stats")
async def get_risk_stats(request: Request):
    engine: TradingEngine = request.app.state.engine
    return engine.risk_manager.stats()
