# ⚡ HFT Trading Tool

A simple but well-structured **High-Frequency Trading backend** built with Python and FastAPI. Designed for learning, portfolio showcasing, and extending into real trading infrastructure.

---

## 🏗️ Architecture

```
hft-trading-tool/
├── src/
│   ├── api/
│   │   ├── main.py              # FastAPI app + lifespan + latency middleware
│   │   └── routes/
│   │       ├── orders.py        # Order CRUD endpoints
│   │       ├── market_data.py   # Order book, tickers, trades
│   │       ├── strategies.py    # Strategy management
│   │       └── portfolio.py     # Positions, PnL, risk
│   ├── core/
│   │   ├── engine.py            # Central trading engine
│   │   ├── order_book.py        # Price-time priority matching engine
│   │   ├── risk_manager.py      # Pre-trade risk checks
│   │   └── models.py            # Order, Trade, Side, OrderStatus
│   ├── strategies/
│   │   ├── base.py              # BaseStrategy + Signal dataclass
│   │   ├── implementations.py   # MarketMaker, MomentumScalper, MeanReversion
│   │   └── registry.py          # Strategy lifecycle management
│   └── utils/
│       └── logger.py            # Structured logging
├── tests/
│   └── test_core.py             # Unit + integration tests
├── requirements.txt
├── pytest.ini
└── README.md
```

---

## 🚀 Features

| Feature | Details |
|---|---|
| **Matching Engine** | Price-time priority using `SortedDict` — O(log n) insert, O(1) best bid/ask |
| **Pre-trade Risk** | Max order size, notional value, price bounds — all O(1) checks |
| **3 Built-in Strategies** | Market Maker, Momentum Scalper, Mean Reversion |
| **Latency Tracking** | Every HTTP response includes `X-Latency-Us` header (microseconds) |
| **Order Lifecycle** | PENDING → OPEN → PARTIALLY_FILLED → FILLED / CANCELLED / REJECTED |
| **Portfolio PnL** | Realised PnL, net positions, unrealised PnL per symbol |
| **Auto-docs** | Swagger UI at `/docs`, ReDoc at `/redoc` |

---

## ⚙️ Setup

```bash
# 1. Clone and enter the project
git clone https://github.com/your-username/hft-trading-tool.git
cd hft-trading-tool

# 2. Create a virtual environment
python -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the server
uvicorn src.api.main:app --reload --port 8000
```

Visit **http://localhost:8000/docs** for the interactive Swagger UI.

---

## 🔌 API Reference

### Orders

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/orders/` | Submit a new order |
| `GET` | `/api/v1/orders/` | List orders (filter by symbol/status) |
| `GET` | `/api/v1/orders/{id}` | Get order by ID |
| `DELETE` | `/api/v1/orders/{id}` | Cancel an open order |

**Submit order example:**
```bash
curl -X POST http://localhost:8000/api/v1/orders/ \
  -H "Content-Type: application/json" \
  -d '{"symbol": "AAPL", "side": "BUY", "quantity": 100, "price": 182.50}'
```

---

### Market Data

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/market/orderbook/{symbol}` | Full order book snapshot (top 10 levels) |
| `GET` | `/api/v1/market/ticker/{symbol}` | Best bid/ask/last trade |
| `GET` | `/api/v1/market/trades` | Recent trades |
| `GET` | `/api/v1/market/symbols` | Active symbols |
| `POST` | `/api/v1/market/seed/{symbol}` | Seed book with simulated liquidity |

**Seed and view order book:**
```bash
# Seed AAPL at $180 mid price
curl -X POST "http://localhost:8000/api/v1/market/seed/AAPL?mid_price=180&levels=5"

# View the order book
curl http://localhost:8000/api/v1/market/orderbook/AAPL
```

---

### Strategies

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/strategies/` | List all strategies |
| `POST` | `/api/v1/strategies/{id}/enable` | Enable a strategy |
| `POST` | `/api/v1/strategies/{id}/disable` | Disable a strategy |

**Available strategy IDs:** `market_maker`, `momentum_scalper`, `mean_reversion`

```bash
# Enable the market maker
curl -X POST http://localhost:8000/api/v1/strategies/market_maker/enable
```

---

### Portfolio

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/portfolio/positions` | Net positions per symbol |
| `GET` | `/api/v1/portfolio/pnl` | Realised PnL breakdown |
| `GET` | `/api/v1/portfolio/risk` | Risk manager stats |

---

### System

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Health check |
| `GET` | `/api/v1/stats` | Engine uptime, fill rate, active strategies |

---

## 🧪 Running Tests

```bash
pytest tests/ -v
```

Expected output:
```
tests/test_core.py::test_order_book_no_match          PASSED
tests/test_core.py::test_order_book_exact_match        PASSED
tests/test_core.py::test_order_book_partial_fill       PASSED
tests/test_core.py::test_order_book_cancel             PASSED
tests/test_core.py::test_order_book_price_priority     PASSED
tests/test_core.py::test_risk_passes_valid_order       PASSED
tests/test_core.py::test_risk_rejects_zero_price       PASSED
tests/test_core.py::test_risk_rejects_zero_quantity    PASSED
tests/test_core.py::test_risk_rejects_large_notional   PASSED
tests/test_core.py::test_engine_submit_and_fill        PASSED
tests/test_core.py::test_engine_cancel_order           PASSED
tests/test_core.py::test_engine_stats                  PASSED
```

---

## 🧠 Strategies Explained

### Market Maker (`market_maker`)
Posts a bid *below* and an ask *above* mid-price by a configurable edge (default: 5 bps). Profits from the bid-ask spread.

### Momentum Scalper (`momentum_scalper`)
Detects directional price movement when spread is tight. Buys on upward momentum, sells on downward momentum.

### Mean Reversion (`mean_reversion`)
When the spread widens beyond a threshold (default: 20 bps), it posts limit orders inside the spread, betting the price will revert.

---

## 🛡️ Risk Controls

All orders pass through pre-trade risk checks before hitting the matching engine:

| Check | Default Limit |
|---|---|
| Min price | $0.0001 |
| Max price | $1,000,000 |
| Max order quantity | 10,000 units |
| Max notional value | $5,000,000 |

Rejected orders are returned immediately with a `reject_reason` and status `REJECTED`.

---

## 📈 Quick Demo Flow

```bash
# 1. Start server
uvicorn src.api.main:app --reload --port 8000

# 2. Seed AAPL order book
curl -X POST "http://localhost:8000/api/v1/market/seed/AAPL?mid_price=180&levels=5"

# 3. Enable market maker strategy
curl -X POST http://localhost:8000/api/v1/strategies/market_maker/enable

# 4. Submit a manual buy order
curl -X POST http://localhost:8000/api/v1/orders/ \
  -H "Content-Type: application/json" \
  -d '{"symbol":"AAPL","side":"BUY","quantity":50,"price":179.90}'

# 5. Check the order book
curl http://localhost:8000/api/v1/market/orderbook/AAPL

# 6. Check positions and PnL
curl http://localhost:8000/api/v1/portfolio/positions
curl http://localhost:8000/api/v1/portfolio/pnl

# 7. Check engine stats
curl http://localhost:8000/api/v1/stats
```

---

## 🔧 Extending the Project

Some ideas to take this further:

- **WebSocket feed** — stream order book updates and trade prints in real time
- **Persistence layer** — swap in Redis or PostgreSQL for order/trade storage
- **Real market data** — connect to a broker WebSocket (Alpaca, Interactive Brokers) to feed live prices
- **Strategy backtesting** — replay historical tick data through the engine
- **Risk circuit breakers** — halt trading on drawdown thresholds
- **Prometheus metrics** — expose latency histograms and fill rates for Grafana

---

## 📄 License

MIT
