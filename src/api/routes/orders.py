"""Orders API — submit, cancel, and query orders."""

import uuid
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field, field_validator
from typing import Optional

from src.core.models import Order, Side, OrderType
from src.core.engine import TradingEngine

router = APIRouter()


class OrderRequest(BaseModel):
    symbol: str = Field(..., example="AAPL")
    side: Side
    quantity: float = Field(..., gt=0, example=100)
    price: float = Field(..., gt=0, example=182.50)
    order_type: OrderType = OrderType.LIMIT

    @field_validator("symbol")
    @classmethod
    def upper_symbol(cls, v):
        return v.upper().strip()


@router.post("/", summary="Submit a new order")
async def submit_order(payload: OrderRequest, request: Request):
    engine: TradingEngine = request.app.state.engine
    order = Order(
        order_id=str(uuid.uuid4()),
        symbol=payload.symbol,
        side=payload.side,
        quantity=payload.quantity,
        price=payload.price,
        order_type=payload.order_type,
    )
    result = await engine.submit_order(order)
    return result.to_dict()


@router.delete("/{order_id}", summary="Cancel an open order")
async def cancel_order(order_id: str, request: Request):
    engine: TradingEngine = request.app.state.engine
    try:
        order = engine.cancel_order(order_id)
        return order.to_dict()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{order_id}", summary="Get order by ID")
async def get_order(order_id: str, request: Request):
    engine: TradingEngine = request.app.state.engine
    order = engine.orders.get(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order.to_dict()


@router.get("/", summary="List all orders (latest 100)")
async def list_orders(request: Request, symbol: Optional[str] = None, status: Optional[str] = None):
    engine: TradingEngine = request.app.state.engine
    orders = list(engine.orders.values())
    if symbol:
        orders = [o for o in orders if o.symbol == symbol.upper()]
    if status:
        orders = [o for o in orders if o.status.value == status.upper()]
    # Sort by timestamp descending, return latest 100
    orders.sort(key=lambda o: o.timestamp_ns, reverse=True)
    return [o.to_dict() for o in orders[:100]]
