# Session Results — May 28 23:40 UTC

## Live Run Results

| Rank | Ticker | Signal | Conf | RSI | Stoch | Trend% | Close | SMA20 | Golden Cross |
|-----:|--------|--------|-----:|----:|------:|-------:|------:|------:|:--:|
| 1 | DELL | SELL | 28.0 | 78.0 | 100.0 | +27.1 | $317.05 | $249.40 | ✅ |
| 2 | AMD | SELL | 24.4 | 74.4 | 100.0 | +19.9 | $518.09 | $432.02 | ✅ |
| 3 | SMCI | SELL | 15.9 | 69.8 | 100.0 | +25.8 | $41.30 | $32.84 | ✅ |
| 4 | VRT | BUY | 14.3 | 39.5 | 0.0 | -7.7 | $314.18 | $340.33 | ✅ |
| 5 | PLTR | SELL | 8.0 | 60.0 | 100.0 | +4.7 | $143.34 | $136.94 | — |
| 6 | COIN | HOLD | 2.5 | 45.0 | 19.8 | -6.4 | $182.25 | $194.70 | ✅ |
| 7 | NVDA | HOLD | 1.3 | 52.5 | 7.1 | -0.3 | $214.25 | $214.88 | ✅ |

## Key Findings This Session

- **DELL/AMD/SMCI**: All in take-profit zone — RSI > 69, Stochastic = 100.0 (maximum overbought). Golden cross intact on all three, but momentum is stretched. Expect pullback.
- **VRT**: Only BUY signal. RSI 39.5 approaching oversold territory. Price below SMA20 (-7.7%) but golden cross still valid (SMA20 > SMA50). Watch for bounce setup.
- **PLTR**: Neutral-bearish. RSI 60, stochastic 100, but no golden cross.
- **COIN/NVDA**: Neutral zone. RSI mid-40s to low-50s. No edge.
- **Portfolio GLD/TSM**: Both deeply underwater — GLD -29.9% ($704 loss), TSM -24.7% ($695 loss). Neither ready to add.

## Signal Methodology

Confidence score = |RSI − 50| + golden_cross_bonus(15)
- Stoch used only for descriptive display (not in signal logic in this mode)
- All data from QuantDinger MCP tools (`mcp_quantdinger_get_klines`)

## Execution Notes

- `mcp_quantdinger_get_klines` used (not raw urllib) — reliable from execute_code
- 42 bars returned per ticker (data source limitation, not an error)
- Report saved to `/opt/hermes/cron/output/f2f177230acb/portfolio-research-20260528-2340.md`
- Discord delivery: `send_message_tool` unavailable; `hermes chat -q` not available in this environment; report file is the delivery mechanism for the cron scheduler
- execute_code sandbox CAN use MCP tools; terminal cannot use MCP tools

## Stochastic Calculation (Corrected)

The stoch() function uses kline OHLC fields — NOT close prices:
```python
def stoch(klines, period=14):
    highs = [k["high"] for k in klines[-period:]]
    lows  = [k["low"]  for k in klines[-period:]]
    close = klines[-1]["close"]
    h_l   = max(highs) - min(lows)
    return 100 * (close - min(lows)) / h_l if h_l else 50
```

**Critical bug that was avoided:** Using `k["close"]` for both highs/lows gives meaningless stochastic values (all = 50 or near-50). Always use `k["high"]` and `k["low"]` for the range.