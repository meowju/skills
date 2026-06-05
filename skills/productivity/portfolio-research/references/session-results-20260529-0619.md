# Session Results — Jun 29 2026 06:19

## Run Summary

Canonical lightweight cron run. Stock universe: VRT, SMCI, PLTR, AMD, NVDA, COIN, DELL.
Portfolio: GLD 4× @ $588.79, TSM 5× @ $563.93.

## Data Quality
- Klines fetched with `limit=200` — returned only **42 bars** (~6 weeks)
- SMA50 **unreliable** for all tickers (bar_count=42 < 55 threshold)
- Golden Cross signals suppressed (s50=None) — this is correct behavior
- Report should include ⚠️ data quality note

## Live Results

| Rank | Ticker | Price | Day% | RSI(14) | SMA20 | Stoch | VolRatio | Signal | Confidence |
|------|--------|------:|-----:|--------:|------:|------:|---------:|--------|----------:|
| 1 | NVDA | $214.25 | +0.78% | 52.5 | 214.88 | 19.7 | 1.09 | HOLD | 48.4 |
| 2 | COIN | $182.25 | +4.87% | 45.0 | 194.70 | 24.6 | 0.76 | HOLD | 42.6 |
| 3 | VRT | $314.18 | -1.75% | 39.5 | 340.33 | 9.5 | 0.95 | **BUY ⬆️** | 39.0 |
| 4 | PLTR | $143.34 | +8.17% | 60.0 | 136.94 | 89.8 | 0.76 | HOLD | 37.6 |
| 5 | DELL | $317.05 | +3.84% | 78.0 | 249.40 | 89.4 | 2.04 | **SELL ⬇️** | 32.5 |
| 6 | SMCI | $41.30 | +8.14% | 69.8 | 32.84 | 84.0 | 1.06 | HOLD | 30.8 |
| 7 | AMD | $518.09 | +4.55% | 74.4 | 432.02 | 93.2 | 0.74 | **SELL ⬇️** | 22.9 |

## Portfolio P&L

| Ticker | Shares | Avg | Current | P&L |
|--------|-------:|----:|-------:|----:|
| GLD | 4 | $588.79 | $412.80 | 📉 -29.89% |
| TSM | 5 | $563.93 | $424.79 | 📉 -24.67% |

## Key Observations

- **VRT** is the only BUY signal — RSI=39.5 (oversold), stochastic %K=9.5 (deeply oversold), price fell -1.75% today. Strong divergence signal.
- **DELL** has RSI=78 + volume ratio 2.04 (massive volume spike) — SELL signal with overbought confirmation.
- **AMD** also overbought (RSI=74.4, stoch=93.2) with weak volume — SELL.
- **NVDA** ranked highest by confidence but it's a HOLD — neutral RSI zone, stoch deeply oversold (19.7) suggests bounce potential but no clear entry yet.
- **GLD and TSM** both ~25-30% underwater — traditional assets not participating in AI rally. Portfolio heavily exposed to non-AI sectors.
- **PLTR +8.17% and SMCI +8.14%** today on high momentum but RSI neutral/overbought — caution flags.

## Report Output Path

`/opt/hermes/cron/output/f2f177230acb/portfolio-research-20260529-0619.md`

## Discord Delivery

Attempted via `send_message_tool` with `discord:stancsz` → **FAILED**: "Platform 'discord' is not configured." Report delivered via file output only (cron scheduler auto-delivers). No Discord skill available in this Hermes environment.