# agentictendies Architecture Reference

## Repo Structure
```
agentictendies/
├── CLAUDE.md              ← Main docs (start here)
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── run_monitor.py         ← CLI: --single-sweep / --loop
├── run_research.py        ← CLI: --run-all --run-advanced --smoke
├── mcp_server.py          ← MCP server (11 tools)
├── import_positions.py    ← CLI: import brokerage CSV (Questrade/Wealthsimple)
├── agentictendies/        ← Python package
│   ├── __init__.py
│   ├── config.py          ← TICKERS, risk params, file paths
│   ├── core/
│   │   ├── indicators.py  ← RSI, ATR, SMA, EMA, momentum — ONE implementation only
│   │   ├── ingestion.py   ← yfinance wrapper (live + historical)
│   │   └── portfolio_math.py ← Ledoit-Wolf shrinkage, MVO, Kelly, Sharpe CI
│   ├── strategies/
│   │   ├── base.py       ← BaseStrategy interface
│   │   ├── sma_crossover.py
│   │   ├── rsi_reversion.py
│   │   ├── macd_crossover.py
│   │   ├── bollinger_reversion.py
│   │   ├── donchian_breakout.py
│   │   └── dual_momentum.py
│   ├── backtester/
│   │   ├── engine.py      ← Vectorized backtests, metrics, optimization
│   │   ├── walk_forward.py ← Rolling walk-forward OOS analysis
│   │   └── monte_carlo.py ← Bootstrap VaR and ruin probability
│   ├── monitoring/
│   │   ├── tracker.py     ← Portfolio ledger, Kelly sizing, trade execution
│   │   ├── signals.py     ← Signal generation (+ LLM fallback)
│   │   └── engine.py      ← Sweep loop with regime filter + drawdown halt
│   └── db/
│       ├── schema.py      ← SQLite schema
│       └── repository.py  ← CRUD for positions, trades
├── research/
│   ├── workbench.py       ← Backtesting workbench
│   ├── gaps.md
│   └── refactor_plan.md
└── data/                  ← SQLite DB, portfolio JSON, trade history
```

## Risk Controls (from CLAUDE.md)
- **Drawdown Halt**: No BUY if portfolio -15% from peak. Resumes when SPY recovers.
- **Regime Filter**: No BUY if SPY below 200-day SMA.
- **Kelly Sizing**: Calculated from trade history, bounded 5–20%, halved for safety.
- **Stops/TP**: 2× ATR stop loss, 3.5× ATR take profit (volatility-adjusted).

## MCP Tools (11 total)
1. `get_portfolio_standing` — valuation, cash, holdings, drawdown, halt status
2. `get_transaction_history` — closed trades w/ realized P&L
3. `get_sweep_report` — last entries from trade_report_log.md
4. `trigger_diagnostic_sweep` — force immediate market scan
5. `emergency_liquidation_halt` — sell all, lock system
6. `reset_portfolio_system` — wipe state, restore $100k cash
7. `get_performance_summary` — CAGR, Sharpe, Sortino, max drawdown active strategies
8. `get_signal_for_ticker` — signal + regime for specific ticker
9. `update_watchlist` — add/remove tickers from live scan
10. `get_market_context` — SPY regime, sector rotation, vol regime
11. `ask_advisor` — Claude-powered trade advisor

## Data Files
- `data/portfolio.json` — live paper portfolio state
- `data/trade_history.json` — all paper trades
- `data/trade_report_log.md` — full audit log

## CLI Usage
```bash
python run_monitor.py --single-sweep   # One scan
python run_monitor.py --loop          # 24/7 continuous
python run_research.py --run-all --run-advanced
python mcp_server.py                  # Start MCP server
```
