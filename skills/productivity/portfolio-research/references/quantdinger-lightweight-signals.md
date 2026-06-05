# QuantDinger-Only Lightweight Signals (No yfinance)

## When to Use This Mode
- 15-minute cron cadence where full backtest + Monte Carlo is overkill
- Need: RSI(14), SMA(20), SMA(50), Stochastic(%K), Volume Ratio, BUY/SELL signal
- No agentictendies import needed — pure inline Python via QuantDinger REST API
- Full backtest + walk-forward approach (yfinance + agentictendies) is in `references/portfolio-cron-workflow.md` for deeper analysis

## Verified Endpoints (May 2026)
```
GET /api/agent/v1/price?market=USStock&symbol=VRT
GET /api/agent/v1/klines?market=USStock&symbol=VRT&timeframe=1d&limit=60
```

Both are live at `http://localhost:8888`. Token from `QUANTDINGER_TOKEN` env var.

## Complete Inline Implementation (Verified May 28 2026)

```python
import urllib.request, json, os
from datetime import datetime

TOKEN = os.environ.get("QUANTDINGER_TOKEN", "")
BASE  = os.environ.get("QUANTDINGER_BASE", "http://localhost:8888")

# ── 1. Fetch klines (for indicators) ───────────────────────────────
ai_stocks = ["VRT", "SMCI", "PLTR", "AMD", "NVDA", "COIN", "DELL"]
all_klines = {}
for sym in ai_stocks:
    req = urllib.request.Request(
        f"{BASE}/api/agent/v1/klines?market=USStock&symbol={sym}&timeframe=1d&limit=60")
    req.add_header("Authorization", f"Bearer {TOKEN}")
    with urllib.request.urlopen(req, timeout=15) as r:
        all_klines[sym] = json.loads(r.read())["data"]["klines"]

# ── 2. Fetch live prices (needed for portfolio tickers GLD/TSM too) ─
all_tickers = ai_stocks + ["GLD", "TSM"]
prices = {}
for sym in all_tickers:
    req = urllib.request.Request(
        f"{BASE}/api/agent/v1/price?market=USStock&symbol={sym}")
    req.add_header("Authorization", f"Bearer {TOKEN}")
    with urllib.request.urlopen(req, timeout=10) as r:
        prices[sym] = json.loads(r.read())["data"]["price"]

# ── 3. Indicator functions (inline, no dependencies) ────────────────
def calc_rsi(closes, period=14):
    """Wilder RSI — ewm(com=period-1) gives same result as SMA-of-gains/losses."""
    if len(closes) < period + 1:
        return None
    deltas = [closes[i] - closes[i-1] for i in range(1, len(closes))]
    gains = [d if d > 0 else 0 for d in deltas[-period:]]
    losses = [-d if d < 0 else 0 for d in deltas[-period:]]
    ag, al = sum(gains) / period, sum(losses) / period
    return 100 - (100 / (1 + ag / al)) if al else 100

def sma(closes, n):
    """Simple moving average of last n closes."""
    return sum(closes[-n:]) / n if len(closes) >= n else None

def stoch(klines, period=14):
    """Stochastic %K = 100 * (close - min_low) / (max_high - min_low)."""
    if len(klines) < period:
        return None
    highs = [k["high"] for k in klines[-period:]]
    lows  = [k["low"]  for k in klines[-period:]]
    close = klines[-1]["close"]
    h_l   = max(highs) - min(lows)
    return 100 * (close - min(lows)) / h_l if h_l else 50

def vol_ratio(klines, period=20):
    """Volume / 20-day average volume."""
    if len(klines) < period:
        return None
    avg = sum(k["volume"] for k in klines[-period:]) / period
    return klines[-1]["volume"] / avg if avg else None

# ── 4. Compute per-ticker signals ────────────────────────────────────
def compute_signal(sym, klines, live_price):
    closes = [k["close"] for k in klines]
    price  = live_price if live_price else closes[-1]
    rsi14  = calc_rsi(closes, 14)
    s20    = sma(closes, 20)
    s50    = sma(closes, 50)
    sk     = stoch(klines)
    vr     = vol_ratio(klines)

    signals = []
    if rsi14 and rsi14 < 40:                    signals.append("BUY")   # oversold
    elif rsi14 and rsi14 > 70:                  signals.append("SELL")  # overbought
    elif rsi14 and 40 <= rsi14 <= 55 and price > (s20 or 0): signals.append("BUY")
    if s20 and s50 and s20 > s50:               signals.append("GOLDEN_CROSS")

    # Confidence: |RSI-50| + golden-cross bonus (15 pts)
    conf = round((abs(rsi14 - 50) if rsi14 else 0)
                 + (15 if "GOLDEN_CROSS" in signals else 0), 1)

    return {
        "price":     round(price, 2),
        "rsi14":     round(rsi14, 1) if rsi14 else None,
        "sma20":     round(s20, 2) if s20 else None,
        "sma50":     round(s50, 2) if s50 else None,
        "stoch":     round(sk, 1) if sk else None,
        "vol_ratio": round(vr, 2) if vr else None,
        "signals":   signals,
        "conf":      conf,
    }

techs = {sym: compute_signal(sym, all_klines[sym], prices.get(sym))
         for sym in ai_stocks if sym in all_klines}
ranked = sorted(techs.items(), key=lambda x: x[1]["conf"], reverse=True)
```

## Signal Logic Summary
| Condition | Signal |
|-----------|--------|
| RSI(14) < 40 | BUY (oversold) |
| RSI(14) > 70 | SELL (overbought) |
| RSI 40–55 AND price > SMA20 | BUY (neutral + trend) |
| SMA20 > SMA50 | GOLDEN_CROSS (adds +15 to confidence) |

**Confidence score** = |RSI − 50| + (15 if golden cross else 0)
Higher = stronger directional conviction.

## Portfolio P&L (Live Prices via /price)
```python
portfolio = [("GLD", 4, 588.79), ("TSM", 5, 563.93)]
for sym, shares, cost in portfolio:
    p = prices.get(sym)
    pnl    = p * shares - cost * shares
    pct    = pnl / (cost * shares) * 100
    # render table row...
```
