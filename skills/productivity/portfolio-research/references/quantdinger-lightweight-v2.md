# QuantDinger Lightweight Signals — Verified Patterns (Jun 2026 Update)

## What's New vs Older Version of This File

- ✅ Correct confidence scoring: bonus when vol_ratio > 1, no penalty below 1
- ✅ SMA50 golden cross gated on bar_count ≥ 55 (fixes false positives from ~42-bar data)
- ✅ Bar count quality gate enforced in `compute_signal()`
- ✅ Price change % tracked per ticker
- ✅ **⚠️ RSI FIX**: Wilder smoothing (pandas ewm) replaces broken simple-last-N-gains sum

---

## Data Fetch Pattern (Verified Jun 2026)

```python
import urllib.request, json, os
from datetime import datetime

TOKEN = os.environ.get("QUANTDINGER_TOKEN", "qd_agent_TWSkB8spR49Kuccw_WMEaVl0L18YyVQG6PaVt6OJ7nM")
BASE  = os.environ.get("QUANTDINGER_BASE", "http://localhost:8888")

ai_stocks = ["VRT", "SMCI", "PLTR", "AMD", "NVDA", "COIN", "DELL"]

# 1. Fetch klines for indicator computation
all_klines = {}
for sym in ai_stocks:
    req = urllib.request.Request(
        f"{BASE}/api/agent/v1/klines?market=USStock&symbol={sym}&timeframe=1d&limit=200")
    req.add_header("Authorization", f"Bearer {TOKEN}")
    with urllib.request.urlopen(req, timeout=15) as r:
        raw = json.loads(r.read())
    # Response shape: {"code":0,"message":"ok","data":{"klines":[...]}}
    all_klines[sym] = raw["data"]["klines"]
    # bar_count = len(klines) — may only be ~42 even with limit=200

# 2. Fetch live prices (needed for portfolio tickers GLD/TSM)
all_tickers = ai_stocks + ["GLD", "TSM"]
prices = {}
for sym in all_tickers:
    req = urllib.request.Request(
        f"{BASE}/api/agent/v1/price?market=USStock&symbol={sym}")
    req.add_header("Authorization", f"Bearer {TOKEN}")
    with urllib.request.urlopen(req, timeout=10) as r:
        prices[sym] = json.loads(r.read())["data"]["price"]
```

---

## Indicator Functions — ⚠️ Use Wilder RSI (not simple last-N)

**⚠️ Critical bug in older version of this file:** the original `calc_rsi` used a simple last-N-gains sum, which gives materially wrong values (e.g. VRT: 39.8 vs 47.0 Wilder). Always use the pandas ewm version below.

```python
import pandas as pd

def calc_rsi(closes, period=14):
    """Wilder-smoothed RSI via pandas ewm (equivalent to Wilder's SMMA)."""
    if len(closes) < period + 1:
        return None
    s = pd.Series(closes)
    delta = s.diff()
    gain  = delta.where(delta > 0, 0.0)
    loss  = (-delta.where(delta < 0, 0.0))
    avg_gain = gain.ewm(com=period-1, min_periods=period).mean().iloc[-1]
    avg_loss = loss.ewm(com=period-1, min_periods=period).mean().iloc[-1]
    return 100 - (100 / (1 + avg_gain/avg_loss)) if avg_loss else 100

def calc_sma(closes, period):
    return sum(closes[-period:])/period if len(closes) >= period else None

def calc_stoch(klines, period=14):
    if len(klines) < period:
        return None
    lows  = [float(k["low"])  for k in klines[-period:]]
    highs = [float(k["high"]) for k in klines[-period:]]
    close = float(klines[-1]["close"])
    h_l   = max(highs) - min(lows)
    return 100*(close - min(lows))/h_l if h_l else 50

def vol_ratio(klines, period=20):
    if len(klines) < period:
        return None
    recent_vol = sum(float(k["volume"]) for k in klines[-5:]) / 5
    avg_vol    = sum(float(k["volume"]) for k in klines[-period:-5]) / (period-5)
    return recent_vol/avg_vol if avg_vol > 0 else 1
```

---

## Signal Computation with Bar-Count Quality Gate

```python
def compute_signal(sym, klines, live_price, bar_count=None):
    closes = [float(k["close"]) for k in klines]
    price  = live_price or closes[-1]

    rsi14  = calc_rsi(closes, 14)
    s20    = calc_sma(closes, 20)
    # ⚠️ SMA50 golden cross only valid when bar_count >= 55 (need 50 + buffer)
    s50    = calc_sma(closes, 50) if (bar_count and bar_count >= 55) else None
    stoch  = calc_stoch(klines)
    vr     = vol_ratio(klines)

    # Signal logic
    if rsi14 and rsi14 < 40:                     sig = "BUY ⬆️"
    elif rsi14 and rsi14 > 70:                   sig = "SELL ⬇️"
    elif rsi14 and 40 <= rsi14 <= 55 and price > (s20 or 0): sig = "BUY ⬆️"
    elif s20 and s50 and s20 > s50:             sig = "GOLDEN CROSS ✡️"  # only if s50 not None
    else:                                        sig = "HOLD"

    # Confidence: max 50 (RSI distance from 50) + trend + volume
    rsi_score   = (50 - abs(rsi14 - 50)) if rsi14 else 0   # 50 at RSI=0 or 100
    trend_score =  20 if (s20 and s50 and s20 > s50) else \
                  -10 if (s50 and s50 > s20) else 0
    vol_score   = max(vr - 1, 0) * 20   # positive bonus for volume spikes; ignore below-1
    confidence  = round(rsi_score + trend_score + vol_score, 1)

    return {
        "price":            round(price, 2),
        "price_chng_pct":   round((closes[-1] - closes[-2])/closes[-2]*100, 2)
                            if len(closes) >= 2 else 0,
        "rsi14":            round(rsi14, 1) if rsi14 else None,
        "sma20":            round(s20, 2)   if s20   else None,
        "sma50":            round(s50, 2)   if s50   else None,  # None when bar_count < 55
        "stoch":            round(stoch, 1) if stoch else None,
        "vol_ratio":        round(vr, 2)    if vr    else None,
        "bar_count":        bar_count,      # always report for SMA50 quality gate
        "signal":           sig,
        "confidence":       confidence,
        "closes":           closes[-5:],
    }

# Apply with bar_count awareness
techs = {}
for sym in ai_stocks:
    bars = len(all_klines.get(sym, []))
    if bars == 0:
        continue
    techs[sym] = compute_signal(sym, all_klines[sym], prices.get(sym), bar_count=bars)

ranked = sorted(techs.items(), key=lambda x: x[1]["confidence"], reverse=True)
```

---

## Confidence Score Design

| Component | Formula | Range |
|-----------|---------|-------|
| RSI distance | `50 - |RSI14 - 50|` | 0–50 |
| Trend (golden cross) | `+20` if SMA20>SMA50 else `0` | -10–+20 |
| Volume spike | `max(vr-1, 0) × 20` | 0–∞ |
| **Total** | sum | 0–∞ |

**Note:** Volume ratio below 1 is not penalized (dry/hungry market still valid signal). Only volume spikes above 1× add to confidence. This prevents stocks in declining volume from being scored downward.

---

## Report Output Template

```markdown
# 📊 AI/基础设施 技术信号报告
> 生成时间: {now} (每15分钟更新)

## 综合排名（按信号置信度）

| 排名 | 股票 | 现价 | 日涨跌 | RSI(14) | SMA20 | 随机K | 成交量比 | 信号 | 置信度 |
|---:|------|-----:|------:|--------:|------:|------:|--------:|------|------: |

{for i, (sym, d) in enumerate(ranked, 1)}
{trend = "📈" if d['price_chng_pct'] > 0 else "📉"}
| {i} | **{sym}** | ${d['price']} | {trend} {d['price_chng_pct']:+.2f}% | {d['rsi14']} | {d['sma20']} | {d['stoch']} | {d['vol_ratio']} | {d['signal']} | {d['confidence']} |

## 信号解读

{for sym, d in ranked}
- **{sym}** — RSI {d['rsi14']} {'🟢 超卖' if d['rsi14'] < 40 else '🔴 超买' if d['rsi14'] > 70 else '🟡 中性'}, 随机K {d['stoch']}, 信号 **{d['signal']}**
```

---

## Output Path

```python
# ✅ CORRECT — Hermes cron scheduler resolves to /opt/hermes/ (hermes home)
out_dir  = "/opt/hermes/cron/output/f2f177230acb"
os.makedirs(out_dir, exist_ok=True)
outpath  = os.path.join(out_dir, f"portfolio-research-{datetime.now():%Y%m%d-%H%M}.md")
discord_path = os.path.join(out_dir, f"discord_msg_{datetime.now():%Y%m%d-%H%M}.txt")

# ❌ WRONG — stale paths from older documentation:
# out_dir = "/opt/data/cron_output/f2f177230acb"      # does not exist
# out_dir = "/opt/data/home/cron/output/"             # wrong user home
# out_dir = "/opt/hermes/cron/output/"               # missing job subdirectory
```

> **Always report bar_count in header** when SMA50 may be unreliable: add `⚠️ 数据质量: {min_bar_count}根K线` when any ticker has < 55 bars.

## Related Session References

- `references/session-results-20260529-1607.md` — live run + Discord delivery notes
- `references/session-results-20260529-1344.md` — Discord delivery failure modes documented