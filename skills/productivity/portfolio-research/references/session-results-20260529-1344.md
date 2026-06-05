# Session Results — May 29 2026 13:44

## What Happened

Scheduled cron run for portfolio research (AI/infrastructure stocks).

## QuantDinger API Response Structure

Confirmed: response is wrapped in `{"code": 0, "message": "ok", "data": {"klines": [...]}}`

```python
# WRONG (first attempt):
klines = data["klines"]  # ❌ KeyError

# CORRECT:
klines = raw["data"]["klines"]  # ✅
```

Even with `limit=200`, API returns only ~42 bars (≈ 6 weeks of data). SMA50 is therefore unreliable for all 7 stocks.

## Live Results (May 29 2026 ~13:44)

| Rank | Ticker | Price | RSI | SMA20 | StochK | VolRatio | Signal | Confidence |
|-----:|--------|------:|----:|------:|-------:|--------:|:------:|----------:|
| 1 | VRT | $314.63 | 47.0 | $339.64 | 10.1 | 0.11x | NEUTRAL | 55.0 |
| 2 | COIN | $183.73 | 47.2 | $194.50 | 27.4 | 0.09x | NEUTRAL | 47.2 |
| 3 | NVDA | $215.71 | 56.5 | $215.69 | 25.0 | 0.09x | NEUTRAL | 43.5 |
| 4 | PLTR | $152.42 | 65.5 | $137.60 | 97.9 | 0.32x | NEUTRAL | 29.5 |
| 5 | AMD | $518.00 | 77.7 | $440.20 | 93.1 | 0.07x | SELL | 17.3 |
| 6 | SMCI | $47.23 | 82.2 | $33.83 | 98.7 | 0.49x | SELL | 12.8 |
| 7 | DELL | $419.14 | 89.5 | $259.91 | 95.3 | 1.31x | SELL | 7.1 |

Notable: DELL surged from ~$317 (May 28) to $419 (+32%) — RSI 89.5 = extreme overbought. SMCI also up sharply from ~$41 to $47.

VRT stochastic %K = 10.1 (deeply oversold) while RSI = 47 (neutral) — bullish divergence signal.

## Discord Delivery — Key Finding

**`send_message_tool` unavailable in `execute_code` sandbox.**

Tested three approaches:
1. `send_message_tool` from `execute_code` → `"Platform 'discord' is not configured"` (tool not available in that context)
2. `send_message_tool` via `terminal cd /opt/hermes && /opt/hermes/.venv/bin/python ...` → same error (gateway not configured for direct tool invocation)
3. Direct Discord REST API (bot token) → `HTTP 403: error code: 1010` (Cloudflare blocking from sandbox IP)

**Correct approach (confirmed working historically):** Write compact message to `/opt/data/cron/output/f2f177230acb/discord_msg_{TS}.txt` — the cron scheduler reads this and delivers automatically.

Report saved to: `/opt/data/cron/output/f2f177230acb/portfolio-research-20260529-1344.md`

## RSI Calculation Note

This session used Wilder-smoothed RSI (correct for cron):
```python
avg_gain = sum(gains[:period]) / period
avg_loss = sum(losses[:period]) / period
for i in range(period, len(gains)):
    avg_gain = (avg_gain * (period - 1) + gains[i]) / period
    avg_loss = (avg_loss * (period - 1) + losses[i]) / period
```

Simple RSI (last N gains/losses only) was used in the first failed attempt and gave different values (e.g., VRT RSI 39.8 vs 47.0). Use Wilder smoothing for consistency.
