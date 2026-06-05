# Session Results — 2026-05-30 04:25 UTC

## Context
15-min cron run. Fetched 7 AI/infra stocks via QuantDinger `/klines` with `limit=200`.

## Key Findings

### QuantDinger klines returned 43 bars (not ~5)
With `limit=200`, the endpoint returned 43 candles — better than the documented ~5 bar limit but still insufficient for SMA50 (needs ≥55).

| Stock | Price | RSI(14) | SMA20 | StochK | VolRatio | Signal | Confidence |
|-------|------:|--------:|------:|-------:|--------:|--------|----------:|
| DELL | $420.91 | 86.8 | 260.0 | 95.9 | 4.32 | SELL | 36.8 |
| SMCI | $46.09 | 75.8 | 33.77 | 88.1 | 2.04 | SELL | 25.8 |
| AMD | $516.10 | 73.8 | 440.11 | 91.7 | 0.77 | SELL | 23.8 |
| PLTR | $156.54 | 71.8 | 137.81 | 95.7 | 2.04 | SELL | 21.8 |
| VRT | $315.71 | 40.3 | 339.69 | 11.6 | 1.26 | HOLD | 9.7 |
| COIN | $189.03 | 48.3 | 194.77 | 37.3 | 1.06 | HOLD | 1.7 |
| NVDA | $211.14 | 49.7 | 215.46 | 8.5 | 1.73 | HOLD | 0.3 |

## Technical Notes

- **RSI**: Standard 14-period Wilder smoothing
- **Stochastic %K**: 14-period raw, no D signal needed
- **Volume ratio**: Last vol / 20-day avg
- **Confidence**: `abs(50 - RSI) + abs(SMA20-SMA50)/SMA50*100` — RSI distance + trend strength
- **Golden cross**: suppressed for all stocks (SMA50 unavailable with 43 bars)
- **Signal logic**: RSI<40=BUY, RSI>70=SELL, RSI 40-55+price>SMA20=BUY

## Updated QuantDinger bar count (Jun 2026)
- `limit=200` → ~43 bars
- `limit=60` → ~43 bars
- SMA50 requires ≥55 → always None for QuantDinger-only data
- SMA20 requires ≥20 → always available
- RSI(14) requires ≥15 → always available

## What Ran Smoothly
- QuantDinger fetch fast and reliable
- Inline RSI/SMA/Stoch/VR computation (no agentictendies needed)
- Signal ranking by confidence sort
- `terminal` heredoc `cat >` avoided Python expanduser bug

## Report Language
Chinese for portfolio commentary/risk language, English for all technical data, tickers, and numeric values.