"""Strategies API — list, enable, disable strategies."""

from fastapi import APIRouter, HTTPException, Request
from src.core.engine import TradingEngine

router = APIRouter()


@router.get("/", summary="List all strategies")
async def list_strategies(request: Request):
    engine: TradingEngine = request.app.state.engine
    return [s.to_dict() for s in engine.strategy_registry.all_strategies()]


@router.post("/{strategy_id}/enable", summary="Enable a strategy")
async def enable_strategy(strategy_id: str, request: Request):
    engine: TradingEngine = request.app.state.engine
    try:
        engine.strategy_registry.enable(strategy_id)
        return {"status": "enabled", "strategy_id": strategy_id}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{strategy_id}/disable", summary="Disable a strategy")
async def disable_strategy(strategy_id: str, request: Request):
    engine: TradingEngine = request.app.state.engine
    try:
        engine.strategy_registry.disable(strategy_id)
        return {"status": "disabled", "strategy_id": strategy_id}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{strategy_id}", summary="Get strategy details")
async def get_strategy(strategy_id: str, request: Request):
    engine: TradingEngine = request.app.state.engine
    try:
        return engine.strategy_registry.get(strategy_id).to_dict()
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
