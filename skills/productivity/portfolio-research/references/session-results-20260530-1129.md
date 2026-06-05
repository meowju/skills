# Session Results — 2026-05-30 11:29 UTC

## Verified Patterns (This Run)

### subprocess+curl pattern — CONFIRMED WORKING
All 7 stocks fetched via `subprocess.run(["curl", ...])` — no SSL context needed:
```
TOKEN = "qd_agent_TWSkB8spR49Kuccw_WMEaVl0L18YyVQG6PaVt6OJ7nM"
BASE  = "http://localhost:8888"
r = subprocess.run(["curl", "-s", "-H", f"Authorization: Bearer {TOKEN}",
                    f"{BASE}/api/agent/v1/klines?market=USStock&symbol={sym}&timeframe=1d&limit=60"],
                   capture_output=True, text=True)
data = json.loads(r.stdout)
bars = data["data"]["klines"]   # ← 43 bars returned regardless of limit
```

### Data Quality (43 bars confirmed)
| Stock | Price  | RSI   | SMA20  | StochK | VolR  | Signal |
|-------|-------:|------:|-------:|-------:|------:|--------|
| VRT   | $315.71| 40.3  | $339.69|   11.6 |  1.26 | HOLD   |
| SMCI  | $46.09 | 73.9  | $33.77|   88.1 |  2.04 | SELL   |
| PLTR  | $156.54| 71.3  | $137.81|   95.7 |  2.04 | SELL   |
| AMD   | $516.10| 67.0  | $440.11|   91.7 |  0.77 | HOLD   |
| NVDA  | $211.14| 46.3  | $215.46|    8.5 |  1.73 | HOLD   |
| COIN  | $189.03| 44.3  | $194.77|   37.3 |  1.06 | HOLD   |
| DELL  | $420.91| 85.1  | $260.00|   95.9 |  4.32 | SELL   |

- 43 bars: enough for RSI(14) + SMA20 — NOT enough for SMA50 (needs ≥50 bars)
- Stochastic K(14) confirmed: deeply oversold for NVDA (8.5), VRT (11.6) — classic buy divergences

## Key Finding
- DELL: RSI=85.1 + StochK=95.9 + Vol×4.32 → extremely overbought, highest confidence SELL
- NVDA: StochK=8.5 (deeply oversold) despite RSI=46.3 (neutral) → bullish divergence
- VRT: RSI=40.3, StochK=11.6 → approaching oversold, approaching buy zone
- COIN: RSI=44.3 → approaching oversold, watch for bounce

## Discord Delivery
File-based pattern used: write to `/opt/data/cron/output/f2f177230acb/discord_msg_20260530-1129.txt`