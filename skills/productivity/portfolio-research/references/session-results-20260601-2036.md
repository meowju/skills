# Session Results: 2026-06-01 20:36

## Context
15-minute cron run for AI/infra stock signals. Complete pipeline: yfinance fetch → indicators → report + Discord delivery.

## Key Finding: yfinance > QuantDinger

QuantDinger was completely abandoned in favor of yfinance:
- **yfinance**: 63 bars returned, clean OHLCV data, correct timestamps
- **QuantDinger**: returned only ~43 bars, JSON nesting required `["data"]["klines"]`, wrong RSI values (e.g. RSI showed -48.2 which is impossible)

**execute_code sandbox issue:** `urllib.request` incorrectly parsed QuantDinger response — the `["data"]["klines"]` path was found only after switching to `subprocess` / terminal, but still yielded wrong bar counts. yfinance via terminal tool is the reliable path.

## Data Source: yfinance

All 11 tickers fetched via yfinance in a single terminal call:
```
VRT: 63 bars, last_close=315.71
SMCI: 63 bars, last_close=46.09
PLTR: 63 bars, last_close=156.54
AMD: 63 bars, last_close=516.10
NVDA: 63 bars, last_close=211.14
COIN: 63 bars, last_close=189.03
DELL: 63 bars, last_close=420.91
GLD: 63 bars, last_close=417.12
TSM: 63 bars, last_close=418.45
SPY: 63 bars, last_close=756.48
^VIX: 64 bars, last_close=15.32
```

## Technical Results

| Stock | Price | RSI(14) | SMA20 | SMA50 | StochK | VolRatio | ATR | Signal | Confidence |
|-------|------:|--------:|------:|------:|-------:|--------:|----:|--------|----------:|
| DELL | $420.91 | 89.4 | 260.00 | 215.62 | 95.9 | 4.32 | 14.87 | SELL | 102.7 |
| SMCI | $46.09 | 79.6 | 33.77 | 28.67 | 88.1 | 2.04 | 3.12 | SELL | 68.5 |
| AMD | $516.10 | 76.0 | 440.11 | 328.15 | 91.7 | 0.77 | 19.73 | SELL | 56.1 |
| TSM | $418.45 | 59.2 | 407.15 | 379.40 | 73.4 | 0.87 | 12.18 | HOLD | 24.2 |
| VRT | $315.71 | 45.3 | 339.69 | 307.36 | 11.6 | 1.26 | 13.77 | HOLD | 19.7 |
| PLTR | $156.54 | 67.6 | 137.81 | 141.79 | 95.7 | 2.04 | 6.98 | HOLD | 17.6 |
| COIN | $189.03 | 48.8 | 194.77 | 189.35 | 37.3 | 1.06 | 6.56 | HOLD | 16.2 |
| NVDA | $211.14 | 49.4 | 215.46 | 199.35 | 8.5 | 1.73 | 5.83 | HOLD | 15.6 |
| GLD | $417.12 | 44.6 | 421.28 | 425.15 | 40.4 | 1.28 | 9.21 | HOLD | 5.4 |

SPY=$756.48 | SMA50=$703.61 | **BEAR** (below SMA50) | VIX=15.3 (MODERATE)

## Portfolio P&L

| Ticker | Shares | Avg Cost | Current | P&L |
|--------|-------:|---------:|--------:|----:|
| GLD | 4 | $588.79 | $417.12 | -$686.68 (-29.2%) |
| TSM | 5 | $563.93 | $418.45 | -$727.40 (-25.8%) |

## Signal Summary

- **SELL**: DELL (RSI=89.4, Stoch=95.9, Vol=4.32x), SMCI (RSI=79.6, Stoch=88.1), AMD (RSI=76.0, Stoch=91.7)
- **HOLD**: VRT (note: RSI=45.3, Stoch=11.6 — watch for BUY signal on further weakness), NVDA, COIN, PLTR, GLD, TSM
- **Market Regime**: SPY=$756.48 < SMA50=$703.61 → **BEAR** → AgenticTendies rules block new BUY trades

## Discord Delivery

- File written to: `/opt/hermes/cron/output/f2f177230acb/discord_msg_20260601-2036.txt`
- Markdown saved to: `/opt/hermes/cron/output/f2f177230acb/portfolio-research-20260601-2036.md`
- Both confirmed written successfully

## Confidence Scoring (from job prompt — not the v2 formula)

```python
if rsi14 and rsi14 < 40:
    signal = "BUY"; confidence = (40 - rsi14) * 2.5
elif rsi14 and rsi14 > 70:
    signal = "SELL"; confidence = (rsi14 - 70) * 2.5
elif rsi14 and 40 <= rsi14 <= 55 and sma20 and last_close > sma20:
    signal = "BUY"; confidence = (55 - rsi14) * 1.5
golden_cross = sma20 and sma50 and sma20 > sma50
if golden_cross and signal == "BUY": confidence += 15
total_score = confidence + abs(50 - rsi14) + (15 if golden_cross else 0)
```

Note: v2 reference (`quantdinger-lightweight-v2.md`) uses a DIFFERENT confidence formula — that file should be treated as historical. The job prompt defines the authoritative formula.
