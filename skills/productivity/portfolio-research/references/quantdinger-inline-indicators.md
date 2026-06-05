# QuantDinger Inline Indicators — Verified Patterns (Jun 2 2026)

Working inline Python implementations for indicators **NOT in** `agentictendies.core.indicators`. Use when computing Stoch K/D or Bollinger Bands directly from QuantDinger klines.

## Why inline?

`agentictendies.core.indicators` (verified via `dir()`) exports only:
`calculate_rsi, calculate_sma, calculate_ema, calculate_atr, calculate_momentum, calculate_volatility_pct, compute_all_indicators`.

It does **NOT** export `calculate_bollinger_bands` or `calculate_stochastic`, despite older report templates and older skill text referencing 布林带 / 随机指标 K/D. Compute them inline.

## Bollinger Bands (20, 2σ)

```python
def bollinger(closes, period=20, num_std=2.0):
    if len(closes) < period:
        return None, None, None
    s = pd.Series(closes, dtype=float)
    mid = s.rolling(period).mean()
    sd  = s.rolling(period).std()
    upper = mid + num_std * sd
    lower = mid - num_std * sd
    return float(upper.iloc[-1]), float(mid.iloc[-1]), float(lower.iloc[-1])

# Position label
def bb_position(price, up, mid, lo):
    if up is None or mid is None or lo is None or up == lo:
        return "N/A"
    if price > up: return "上轨"
    if price < lo: return "下轨"
    if price > mid: return "中轨"
    return "中轨"
```

## Stochastic %K / %D (14, 3, 3)

```python
def stoch_kd(klines, period=14, k_smooth=3, d_smooth=3):
    if len(klines) < period + k_smooth + d_smooth:
        return None, None
    closes = pd.Series([k["close"] for k in klines])
    lows   = pd.Series([k["low"]  for k in klines])
    highs  = pd.Series([k["high"] for k in klines])
    hh = highs.rolling(period).max()
    ll = lows.rolling(period).min()
    raw_k = 100 * (closes - ll) / (hh - ll).replace(0, pd.NA)
    raw_k = raw_k.fillna(50.0)
    k = raw_k.rolling(k_smooth).mean()
    d = k.rolling(d_smooth).mean()
    return float(k.iloc[-1]), float(d.iloc[-1])
```

## MACD with histogram

```python
from agentictendies.core.indicators import calculate_ema

def macd_state(closes):
    if len(closes) < 35:
        return None, None, None, None
    s = pd.Series(closes, dtype=float)
    ema12 = calculate_ema(s, 12)
    ema26 = calculate_ema(s, 26)
    macd = ema12 - ema26
    signal = calculate_ema(macd, 9)
    hist = macd - signal
    return (float(macd.iloc[-1]), float(signal.iloc[-1]),
            float(hist.iloc[-1]),
            "BULL" if macd.iloc[-1] > signal.iloc[-1] else "BEAR")
```

## Volume Ratio (today vs 20d avg, excluding today)

```python
def vol_ratio(klines, lookback=20):
    if len(klines) < lookback:
        return None
    vols = [float(k.get("volume", 0)) for k in klines[-lookback:]]
    avg = sum(vols[:-1]) / (lookback - 1) if vols[:-1] else 0
    return vols[-1] / avg if avg > 0 else 1.0
```

## Confidence Score (used by Jun 2 cron)

```python
rsi_dist = abs(rsi - 50)
trend_pct = (last_close - sma20) / sma20 * 100
confidence = round(rsi_dist + abs(trend_pct) * 0.5, 2)
```

## Signal Logic (priority order)

1. RSI < 40 → 🟢 BUY
2. RSI > 70 → 🔴 SELL
3. RSI 40-55 + price > SMA20 → 🟢 BUY
4. RSI 40-55 + price ≤ SMA20 → 🟡 HOLD
5. RSI 55-70 → 🔴 SELL (overbought zone)
6. Otherwise → 🟡 HOLD

## Verified Run Output (Jun 2 2026 11:34, QuantDinger klines via `limit=250`)

| Ticker | Price | RSI(14) | SMA20 | SMA50 | Stoch K/D | VolRatio | BB Pos | Signal | Conf |
|---|---:|---:|---:|---:|---:|---:|:---:|:---:|---:|
| DELL | 465.96 | 91.3 | 272.79 | 221.81 | 94.6/93.2 | x2.06 | 上轨 | SELL | 76.69 |
| SMCI | 46.88 | 80.3 | 34.76 | 28.99 | 88.1/88.6 | x1.07 | 上轨 | SELL | 47.69 |
| AMD | 510.13 | 73.7 | 447.58 | 334.24 | 90.7/91.4 | x0.83 | 中轨 | SELL | 30.69 |
| PLTR | 160.65 | 70.0 | 138.64 | 141.89 | 92.3/75.3 | x1.25 | 上轨 | SELL | 27.9 |
| NVDA | 224.36 | 60.4 | 216.75 | — | 28.1/24.0 | x1.26 | 中轨 | SELL | 12.15 |
| COIN | 182.61 | 45.3 | 194.34 | — | 29.1/19.6 | x0.92 | 中轨 | HOLD | 7.67 |
| VRT | 323.39 | 49.1 | 339.45 | — | 14.4/12.9 | x1.06 | 中轨 | HOLD | 3.3 |

> DELL/SMCI/AMD/PLTR all show **real SMA50 values** — QuantDinger `/klines?limit=250` returned >55 bars for these tickers. NVDA/COIN/VRT returned slightly fewer (still showed SMA20, stochastic, MACD). Always gate Golden Cross on `bar_count >= 55` per ticker.
