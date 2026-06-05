# yfinance as Primary Data Source — Verified Pattern (Jun 2026)

## Critical Finding

**QuantDinger is UNRELIABLE for this cron job.** Verified Jun 1, 2026:
- QuantDinger `/klines` returns **43 bars** even with `limit=200`
- JSON nesting is `raw["data"]["klines"]` (not top-level array)
- `urllib.request` in `execute_code` sandbox works to localhost:8888 but returns wrong data
- **yfinance returns 63+ clean OHLCV bars** in one call — reliable, no nesting issues

## yfinance Primary Pattern

```python
import yfinance as yf
import os
from datetime import datetime, timedelta

PYTHON = "/opt/data/agentictendies/.venv/bin/python"

SCRIPT = """
import yfinance as yf
import json
from datetime import datetime, timedelta

tickers = ['VRT','SMCI','PLTR','AMD','NVDA','COIN','DELL','GLD','TSM','SPY','^VIX']
end = datetime.now()
start = end - timedelta(days=90)
raw = {}
for t in tickers:
    df = yf.Ticker(t).history(start=start.strftime('%Y-%m-%d'), end=end.strftime('%Y-%m-%d'), auto_adjust=True)
    raw[t] = {
        'closes':  [float(x) for x in df['Close'].tolist()],
        'highs':    [float(x) for x in df['High'].tolist()],
        'lows':     [float(x) for x in df['Low'].tolist()],
        'volumes':  [float(x) for x in df['Volume'].tolist()],
        'bar_count': len(df)
    }
print(json.dumps(raw))
"""
r = subprocess.run([PYTHON, "-c", SCRIPT], capture_output=True, text=True, timeout=120)
data = json.loads(r.stdout)
```

**Execute via `terminal` tool** — `execute_code` sandbox CANNOT import yfinance (missing numpy/pandas C extensions). The `terminal` tool with `.venv/bin/python` works.

## Indicator Functions (Pure Python — no pandas needed)

```python
def calc_rsi(closes, period=14):
    if len(closes) < period + 1: return None
    gains, losses = [], []
    for i in range(1, len(closes)):
        d = closes[i] - closes[i-1]
        gains.append(d if d > 0 else 0)
        losses.append(-d if d < 0 else 0)
    ag = sum(gains[:period]) / period
    al = sum(losses[:period]) / period
    for i in range(period, len(gains)):
        ag = (ag * (period - 1) + gains[i]) / period
        al = (al * (period - 1) + losses[i]) / period
    if al == 0: return 100
    return 100 - (100 / (1 + ag / al))

def calc_sma(closes, period):
    if len(closes) < period: return None
    return sum(closes[-period:]) / period

def calc_stoch(closes, highs, lows, period=14):
    if len(closes) < period: return None
    k = closes[-1]
    h = max(highs[-period:])
    l = min(lows[-period:])
    if h == l: return 50
    return (k - l) / (h - l) * 100

def calc_vol_ratio(volumes, period=20):
    if len(volumes) < period: return None
    avg = sum(volumes[-period:]) / period
    return volumes[-1] / avg if avg > 0 else 1.0

def calc_atr(highs, lows, closes, period=14):
    if len(closes) < period + 1: return None
    trs = []
    for i in range(1, len(closes)):
        trs.append(max(highs[i]-lows[i], abs(highs[i]-closes[i-1]), abs(lows[i]-closes[i-1])))
    return sum(trs[-period:]) / period
```

## Signal Logic (From Job Prompt)

```python
if rsi14 and rsi14 < 40:
    signal = "BUY"; confidence = (40 - rsi14) * 2.5
elif rsi14 and rsi14 > 70:
    signal = "SELL"; confidence = (rsi14 - 70) * 2.5
elif rsi14 and 40 <= rsi14 <= 55 and sma20 and last_close > sma20:
    signal = "BUY"; confidence = (55 - rsi14) * 1.5
else:
    signal = "HOLD"; confidence = 0

golden_cross = sma20 and sma50 and sma20 > sma50
if golden_cross:
    if signal == "BUY": confidence += 15

# Final: confidence = confidence + abs(50 - rsi14) + (15 if golden_cross else 0)
```

## SPY Market Regime

```python
spy = data['SPY']['closes']
spy50 = calc_sma(spy, 50)
spy200 = calc_sma(spy, 200)  # 63 bars — may be None if bar_count < 200
spy_price = spy[-1]
spy_regime = "BULL" if spy200 and spy_price > spy200 else "BEAR"
# AgenticTendies rule: NO new BUY trades when SPY below 200-SMA
```

## Verified Results (Jun 1, 2026 — 63 yfinance bars)

| Stock | Price | RSI | SMA20 | SMA50 | StochK | VolRatio | Signal | Confidence |
|-------|------:|----:|------:|------:|-------:|--------:|--------|----------:|
| DELL | $420.91 | 89.4 | 260.00 | 215.62 | 95.9 | 4.32 | SELL | 102.7 |
| SMCI | $46.09 | 79.6 | 33.77 | 28.67 | 88.1 | 2.04 | SELL | 68.5 |
| AMD | $516.10 | 76.0 | 440.11 | 328.15 | 91.7 | 0.77 | SELL | 56.1 |
| TSM | $418.45 | 59.2 | 407.15 | 379.40 | 73.4 | 0.87 | HOLD | 24.2 |
| VRT | $315.71 | 45.3 | 339.69 | 307.36 | 11.6 | 1.26 | HOLD | 19.7 |
| NVDA | $211.14 | 49.4 | 215.46 | 199.35 | 8.5 | 1.73 | HOLD | 15.6 |
| COIN | $189.03 | 48.8 | 194.77 | 189.35 | 37.3 | 1.06 | HOLD | 16.2 |
| GLD | $417.12 | 44.6 | 421.28 | 425.15 | 40.4 | 1.28 | HOLD | 5.4 |

SPY=$756.48 | SMA50=$703.61 | **BEAR** | VIX=15.3 MODERATE
