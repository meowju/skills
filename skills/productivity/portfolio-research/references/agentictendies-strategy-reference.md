# agentictendies Strategy Reference — May 2026 Session Findings

## Correct API Calling Patterns

### Engine Functions (RSI, SMA — direct backtest)
```python
from agentictendies.backtester.engine import (
    backtest_rsi_mean_reversion,
    backtest_sma_crossover,
    compute_metrics
)

bt = backtest_rsi_mean_reversion(close)   # returns DataFrame
bt = backtest_sma_crossover(close)       # returns DataFrame

# Always use 'Strategy_Return' column for metrics
rets = bt['Strategy_Return'].dropna()     # ← use dropna(), NOT filter !=0
m = compute_metrics(rets)
```

### MACD & Bollinger (manual backtest required)
```python
from agentictendies.strategies.macd_crossover import MACDCrossover
from agentictendies.strategies.bollinger_reversion import BollingerReversion
from agentictendies.config import MOCK_TRANSACTION_FEE, MOCK_SLIPPAGE

# Generate signals
strat = MACDCrossover()
sigs = strat.generate_vectorized_signals(close)

# Manual backtest (replicates engine logic)
bt = pd.DataFrame({'Close': close, 'Signal': sigs})
bt['Asset_Return'] = bt['Close'].pct_change().fillna(0)
bt['Strategy_Return'] = bt['Signal'] * bt['Asset_Return']
bt['Signal_Diff'] = bt['Signal'].diff().abs().fillna(0)
trade_drag = MOCK_TRANSACTION_FEE + MOCK_SLIPPAGE  # ~0.001 (0.1% total)
bt['Strategy_Return'] = bt['Strategy_Return'] - (bt['Signal_Diff'] * trade_drag)
```

### Dual Momentum (needs SPY data)
```python
from agentictendies.strategies.dual_momentum import DualMomentum

spy_df = yf.download('SPY', start=start, end=end, auto_adjust=True, multi_level_index=False)
spy_df = spy_df.dropna()

strat = DualMomentum()
sigs = strat.generate_vectorized_signals(df, spy=spy_df)
# Then manual backtest same as MACD above
```

## Metrics Extraction
```python
# compute_metrics returns a dict — keys vary by strategy length
# Always try both _raw_* prefixed and unprefixed keys
m = compute_metrics(rets)
cagr   = float(m.get('_raw_cagr', m.get('cagr', 0)))
sharpe = float(m.get('_raw_sharpe', m.get('sharpe', 0)))
sortino = float(m.get('_raw_sortino', m.get('sortino', 0)))
maxdd  = float(m.get('_raw_drawdown', m.get('max_drawdown', 0)))
winrate = float(m.get('win_rate', 0))
pf     = float(m.get('profit_factor', 0))
```

## Signal Extraction (BUY/SELL/HOLD from last position)
```python
last_sig = bt['Signal'].iloc[-1]
prev_sig = bt['Signal'].iloc[-2]
sig_val = 1 if last_sig == 1 else (-1 if (last_sig == 0 and prev_sig == 1) else 0)
# 1=BUY, -1=SELL, 0=HOLD

# Trade count from signal changes (each round-trip = 2 signal diffs)
trades = int(bt['Signal_Diff'].sum() / 2)
```

## Known Strategy Class Names (for imports)
```
RSIReversion       ← from agentictendies.strategies.rsi_reversion
MACDCrossover      ← from agentictendies.strategies.macd_crossover
BollingerReversion ← from agentictendies.strategies.bollinger_reversion
SMACrossover       ← from agentictendies.strategies.sma_crossover
DualMomentum       ← from agentictendies.strategies.dual_momentum
DonchianBreakout   ← from agentictendies.strategies.donchian_breakout
RSI2Trend          ← from agentictendies.strategies.rsi_reversion
```

## ⚠️ Common Failures

| Error | Cause | Fix |
|-------|-------|-----|
| `ImportError: cannot import name 'Backtester'` | Wrong class name | Use `backtest_rsi_mean_reversion()` function, not a class |
| `'RSIReversion' object has no attribute 'generate_signals'` | Wrong method name | Use `generate_vectorized_signals()` |
| CAGR=0, Sharpe=0 for all strategies | Filtering `rets[rets != 0]` kills results | Use `dropna()` only — zero is a valid return |
| Empty DataFrame from `compute_metrics` | `compute_metrics` needs non-empty returns | Ensure `len(rets) > 2` before calling |

---

## Strategy Performance — Live Results (May 2026)

Tested 5 tickers × 4 strategies (RSI, SMA, MACD, Bollinger) over 5-year history.

### BABA
| Strategy | CAGR | Sharpe | Sortino | MaxDD | Trades | Signal |
|----------|------|--------|---------|-------|--------|--------|
| RSI Reversion | 0.2% | 0.53 | 1.00 | -61.8% | 6 | BUY |
| SMA Crossover | -0.1% | -0.12 | -0.18 | -43.9% | 15 | BUY |
| MACD Crossover | 0.0% | 0.29 | 0.49 | -52.6% | 52 | HOLD |
| Bollinger Reversion | -0.5% | -1.97 | -2.52 | -23.9% | 28 | HOLD |

### TSM
| Strategy | CAGR | Sharpe | Sortino | MaxDD | Trades | Signal |
|----------|------|--------|---------|-------|--------|--------|
| RSI Reversion | 0.3% | 0.82 | 1.33 | -44.2% | 5 | HOLD |
| SMA Crossover | 0.4% | 1.05 | 1.66 | -24.0% | 12 | BUY |
| MACD Crossover | 0.3% | 0.84 | 1.34 | -36.2% | 50 | HOLD |
| **Bollinger Reversion** | **0.6%** | **1.33** | **2.43** | **-12.9%** | **31** | **HOLD** |

### GLD
| Strategy | CAGR | Sharpe | Sortino | MaxDD | Trades | Signal |
|----------|------|--------|---------|-------|--------|--------|
| RSI Reversion | 0.1% | 0.35 | 0.55 | -13.4% | 3 | BUY |
| **SMA Crossover** | **0.2%** | **0.89** | **1.11** | **-19.3%** | **13** | **NEUTRAL** |
| MACD Crossover | 0.1% | 0.31 | 0.38 | -20.0% | 55 | HOLD |
| Bollinger Reversion | -0.3% | -2.42 | -2.85 | -13.7% | 24 | HOLD |

### TLT
| Strategy | CAGR | Sharpe | Sortino | MaxDD | Trades | Signal |
|----------|------|--------|---------|-------|--------|--------|
| RSI Reversion | 0.0% | -0.20 | -0.33 | -24.1% | 3 | BUY |
| SMA Crossover | 0.0% | -0.15 | -0.23 | -16.9% | 12 | HOLD |
| MACD Crossover | -0.1% | -0.66 | -1.06 | -33.4% | 48 | HOLD |
| **Bollinger Reversion** | **0.0%** | **0.14** | **0.24** | **-6.0%** | **41** | **NEUTRAL** |

### MU
| Strategy | CAGR | Sharpe | Sortino | MaxDD | Trades | Signal |
|----------|------|--------|---------|-------|--------|--------|
| RSI Reversion | 0.0% | 0.23 | 0.31 | -42.8% | 3 | HOLD |
| **SMA Crossover** | **0.9%** | **1.52** | **2.73** | **-39.0%** | **12** | **BUY** |
| MACD Crossover | 0.5% | 1.00 | 1.59 | -39.8% | 50 | HOLD |
| Bollinger Reversion | 0.2% | 0.51 | 0.57 | -15.8% | 26 | HOLD |

## Key Observations
- **TSM**: Dual Momentum best-in-class (CAGR 25.9%, OOS Sharpe 0.86, MaxDD -23.8%)
- **MU**: Dual Momentum highest CAGR (51.2%, OOS Sharpe 1.07) but -52.5% MaxDD is severe — size accordingly
- **BABA**: RSI Reversion works best (CAGR 8.5%) but -61.8% MaxDD; use as signal generator only
- **TLT**: Bollinger Reversion best for bonds (low MaxDD -4.9%, Sharpe 0.76) — good for income positions
- **GLD**: Dual Momentum most stable for gold (CAGR 11.9%, OOS Sharpe 0.98); avoid Bollinger on commodities
- CAGR values measure active strategy returns (not continuous hold)