# AgenticTendies indicators — what to import

Per `agentictendies/CLAUDE.md`: **"All indicator math in `core/indicators.py`. Never duplicate logic."** So always import.

## Available (as of this writing)

```python
import sys
sys.path.insert(0, "/opt/data/agentictendies")
from agentictendies.core.indicators import (
    calculate_rsi,        # RSI(period) — EMA-smoothed
    calculate_sma,        # SMA(window)
    calculate_ema,        # EMA(span)
    calculate_atr,        # ATR(period) — OHLC
    calculate_volatility_pct,  # ATR / close * 100
    calculate_momentum,   # 12-month total return %
    compute_all_indicators,    # Convenience: all of the above + SMA_20/50/200, EMA_50
)
```

## Function signatures (from `core/indicators.py`)

```python
def calculate_rsi(prices: pd.Series, window: int = 14) -> pd.Series
def calculate_sma(prices: pd.Series, window: int) -> pd.Series
def calculate_ema(prices: pd.Series, span: int) -> pd.Series
def calculate_atr(high: pd.Series, low: pd.Series, close: pd.Series, window: int = 14) -> pd.Series
def calculate_volatility_pct(atr: pd.Series, close: pd.Series) -> pd.Series
def calculate_momentum(prices: pd.Series, lookback: int = 252) -> pd.Series
def compute_all_indicators(df: pd.DataFrame) -> pd.DataFrame
```

## What compute_all_indicators adds

After `compute_all_indicators(df)`:

| Column | Description |
|---|---|
| `SMA_20`, `SMA_50`, `SMA_200` | Simple moving averages |
| `EMA_50` | Exponential MA, span=50 |
| `RSI` | RSI(14) |
| `ATR` | ATR(14) |
| `ATR_Pct` | ATR as % of close |

Note the suffix convention: `compute_all_indicators` uses `RSI`, `SMA_20`, etc. (underscore-number), while the bare `calculate_*` functions return the raw series. Pick the convention you import under; don't mix `df["RSI"]` and `df["rsi14"]` in the same script.

## Not in the framework — compute inline

- **Stochastic %K(14,3)**: `%K = 100 * (close - lowest_low_14) / (highest_high_14 - lowest_low_14)`, then `.rolling(3).mean()`.
- **Bollinger Bands**, **MACD line/signal/histogram**, **OBV**: write inline if you need them; do not duplicate RSI/SMA/EMA/ATR inline.
- **Volume ratio**: `df["volume"] / df["volume"].rolling(20).mean()`. Trivial, no need to wrap.

## Gotchas

- RSI uses EMA smoothing (RMA/SMMA with `com=window-1`), not Wilder's classic rolling-mean. Both are common; the difference is small for steady markets but visible at the extremes. Document the choice in any backtest that depends on RSI threshold.
- SMA returns NaN for the first `window-1` bars. Always guard with `has(v)` before formatting.
- ATR is the simple rolling mean of true range, **not** Wilder-smoothed. If you compare against TradingView, expect small differences.
- `compute_all_indicators` requires columns named `Open High Low Close Volume` (capitalized). Rename before calling.
