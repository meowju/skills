# Verified Indicator Patterns (May 2026 Session)

These patterns were used successfully in the 18:59 cron run and proved more reliable than rolling-window custom approaches. Use them as the canonical implementation.

## Data Fetching

**Dict-of-dicts restructuring from MultiIndex yfinance response:**

```python
import yfinance as yf
import pandas as pd

tickers = ["SPY", "VRT", "SMCI", "SYM", "PLTR", "DELL", "AMD", "NVDA", "COIN", "GLD", "TSM"]
result = {}

for t in tickers:
    df = yf.download(t, period="5y", progress=False)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    C = df['Close'].dropna()
    V = df['Volume'].dropna()
    H = df['High']
    L = df['Low']
    
    cp = float(C.iloc[-1])
    pc = float(C.iloc[-2]) if len(C) > 1 else cp
    daily_ret = round((cp - pc) / pc * 100, 3)
    # ... indicator calculations ...
```

## Indicators (All Inline)

### RSI(14)
```python
deltas = C.diff()
gains = deltas.clip(lower=0)
losses = (-deltas).clip(lower=0)
ag = gains.ewm(com=13, adjust=False).mean()
al = losses.ewm(com=13, adjust=False).mean()
rsi = round(float((100 - (100 / (1 + ag / al))).iloc[-1]), 1)
```

### MACD(12,26,9)
```python
e12 = C.ewm(span=12).mean()
e26 = C.ewm(span=26).mean()
dif = e12 - e26
dea = dif.ewm(span=9).mean()
hist = dif - dea
macd_v = round(float(dif.iloc[-1]), 3)
macd_s = round(float(dea.iloc[-1]), 3)
macd_h = round(float(hist.iloc[-1]), 3)
```

### ATR(14) — Wilder Method
```python
tr1 = H - L
tr2 = (H - C.shift()).abs()
tr3 = (L - C.shift()).abs()
tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
atr = round(float(tr.ewm(com=13, adjust=False).mean().iloc[-1]), 2)
```

### Bollinger Bands(20,2)
```python
s20 = C.rolling(20).mean()
std20 = C.rolling(20).std()
bb_u = round(float((s20 + 2*std20).iloc[-1]), 2)
bb_l = round(float((s20 - 2*std20).iloc[-1]), 2)
```

### SMA(50/200) and EMA(20)
```python
sma50 = round(float(C.rolling(50).mean().iloc[-1]), 2)
sma200 = round(float(C.rolling(200).mean().iloc[-1]), 2)
ema20 = round(float(C.ewm(span=20).mean().iloc[-1]), 2)
```

### Volume Ratio
```python
vol_rat = round(float(V.iloc[-1] / V.rolling(20).mean().iloc[-1]), 2)
```

## Walk-Forward (agentictendies Built-in)

```python
from agentictendies.backtester.walk_forward import run_walk_forward

oos_rets, oos_eq, wfa_log = run_walk_forward(prices)  # returns TUPLE
oos_clean = oos_rets.dropna()
sharpe = round(float(oos_clean.mean() / oos_clean.std() * np.sqrt(252)), 3) if oos_clean.std() > 0 else 0.0

# WFA results from May 2026 session:
# VRT: 1.53, NVDA: 1.23, DELL: 1.05, PLTR: 0.96, SMCI: 0.78, AMD: 0.66, SYM: 0.29, COIN: -0.13
```

## Monte Carlo (Inline, 1000 runs)

```python
import numpy as np

C = df['Close'].dropna()
rets = C.pct_change().dropna()
mu = float(rets.mean())
sigma = float(rets.std())

n_runs = 1000
n_days = 21
np.random.seed(42)

# VaR: drawdown distribution across all paths
sim_returns = np.random.normal(mu, sigma, (n_runs, n_days))
var_95_1d_pct = round(float(np.percentile(sim_returns, 5) * 100), 2)

# MaxDD: for each path, compute peak-to-trough drawdown
sim_dds = []
for i in range(200):  # reduced for speed, increase to 1000 for full
    path = C.iloc[-1] * np.cumprod(1 + np.random.normal(mu, sigma, n_days))
    peak = np.maximum.accumulate(path)
    dd = (path - peak) / peak
    sim_dds.append(float(dd.min()))
max_dd_pct = round(float(np.mean(sim_dds)) * 100, 2)

# Annualized volatility
ann_vol = round(float(sigma * np.sqrt(252) * 100), 1)
```

**Known VaR/MaxDD results (May 2026 session):**
| Ticker | VaR 95%（日） | MaxDD 1M | AnnVol |
|--------|------------:|--------:|----------:|
| GLD | -1.93% | -4.67% | 20.0% |
| TSM | -3.70% | -8.78% | 38.2% |
| SPY | -1.47% | -3.56% | 15.1% |
| VRT | -5.93% | -13.43% | 62.1% |
| SMCI | -9.68% | -23.13% | 96.6% |
| NVDA | -4.55% | -10.76% | 46.9% |

## Combined Signal Logic

```python
# From indicators: rsi, macd_hist, sma50, sma200, price, vol_ratio, wfa_sharpe, atr

def signal_for_ticker(d, wfa_sharpe):
    rsi = d['rsi14']
    macd_h = d['macd_hist']
    price = d['price']
    atr = d['atr14']
    
    # Entry / Stop / Target
    if atr > 0:
        stop = round(price - 2 * atr, 2)
        target = round(price + 3.5 * atr, 2)
    else:
        stop = round(price * 0.92, 2)
        target = round(price * 1.18, 2)
    
    # Signal: MACD histogram direction + RSI zone
    if macd_h > 0 and rsi < 70:
        base_sig = "BUY"
    elif macd_h < -1.5 and rsi > 60:
        base_sig = "SELL"
    else:
        base_sig = "HOLD"
    
    # Confidence from WFA Sharpe
    confidence = int(min(95, max(40, 40 + wfa_sharpe * 30)))
    
    # Special cases
    if wfa_sharpe < 0:
        base_sig = "SELL"
        confidence = max(60, 65 + wfa_sharpe * 20)
    if rsi > 75:
        confidence = min(confidence, 60)  # cap confidence in overbought
    
    return base_sig, confidence, stop, target
```

## Portfolio Position Table

```python
positions = {"GLD": {"shares": 4, "avg_cost": 588.79}, "TSM": {"shares": 5, "avg_cost": 563.93}}

for t, meta in positions.items():
    cp = current_prices[t]
    shares = meta["shares"]
    avg = meta["avg_cost"]
    cost = shares * avg
    mv = shares * cp
    pnl = mv - cost
    pnl_pct = round(pnl / cost * 100, 1)
    ret_pct = round((cp - avg) / avg * 100, 1)
```

**Current portfolio results (May 27, 18:59):**
- GLD: mv=$1,635, pnl=-$720 (-30.6%), RSI 36.7, MACD hist -1.199, signal=BEARISH
- TSM: mv=$2,107, pnl=-$713 (-25.3%), RSI 62.3, MACD hist -0.441, signal=NEUTRAL
- Total: cost=$5,175, mv=$3,742, pnl=-$1,433 (-27.7%)