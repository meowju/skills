# Session Results — May 30 17:32

## Key Finding: urllib.request BROKEN in execute_code sandbox (HTTP 401)

**Root cause identified:** `urllib.request.urlopen` in the `execute_code` sandbox returns HTTP 401 to QuantDinger even with:
- SSL context (`ssl.create_default_context()` with `CERT_NONE`)
- Correct Bearer token
- Direct localhost URL (no DNS/SSL cert issues)

This is a sandbox networking isolation issue, NOT an SSL problem. The SSL context fix documented in previous sessions was a red herring for this particular failure mode.

**Verified working:** `subprocess.run(["curl", ...])` with hardcoded token — works from both `execute_code` sandbox AND `terminal` tool.

**QuantDinger klines response shape confirmed:**
- Path: `raw["data"]["klines"]` (not `raw["klines"]`)
- Bar count: ~43 bars regardless of `limit` parameter (limit=5, 60, 200 all tested)
- SMA50 unreliable (need ≥55 bars); SMA20 and RSI(14) always available

## Live Results (May 30 17:32 UTC)

| Stock | Price | RSI(14) | SMA20 | StochK | VolRatio | Signal | Confidence |
|-------|------:|--------:|------:|-------:|--------:|--------|----------:|
| DELL | $420.91 | 85.1 🔴 | $260.0 | 95.9 | 2.12 | SELL | 37.7 |
| SMCI | $46.09 | 73.9 🔴 | $33.77 | 88.1 | 1.26 | SELL | 9.8 |
| PLTR | $156.54 | 71.3 🟡 | $137.81 | 95.7 | 1.05 | SELL | 3.2 |
| VRT | $315.71 | 40.3 🟢 | $339.69 | 11.6 | 1.02 | HOLD | 0 |
| AMD | $516.10 | 67.0 🟡 | $440.11 | 91.7 | 0.82 | HOLD | 0 |
| NVDA | $211.14 | 46.3 🟢 | $215.46 | 8.5 | 1.15 | HOLD | 0 |
| COIN | $189.03 | 44.3 🟢 | $194.77 | 37.3 | 0.89 | HOLD | 0 |

**Actionable:** DELL/SMCI/PLTR all SELL (overbought). No BUY signals. VRT and COIN near oversold — watch for breakout.
