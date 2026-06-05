---
name: hermes-cron-jobs
description: Running as a scheduled Hermes cron job — the delivery model, paths, and tooling pitfalls. Use whenever you're invoked by the Hermes cron harness (job id like `f2f177230acb`) and need to produce a periodic report that gets auto-delivered to Discord DM, webhook, or other channel.
---

# Hermes Scheduled Jobs

When you're running as a scheduled cron job in Hermes (portfolio research, market scans, hourly monitors, etc.) the runtime model is **not** the same as a normal user session. Most session-shaped instincts are wrong here.

## 1. Delivery model — you don't send anything

The job's `deliver` field in `/opt/data/cron/jobs.json` is what actually reaches the user. The cron harness forwards your final response to that destination (Discord DM, webhook, email, etc.) after the run finishes.

**Do:**
- Put the report content directly in your final assistant message.
- Treat the markdown report as the deliverable.

**Don't:**
- Don't call any `send_message` / Discord / webhook tool — you don't have one. There is no message-sending tool in cron context.
- Don't try to POST to a Discord webhook directly — the harness already handles it.
- Don't write to a `sent/` directory or move files out of `output/`.

**Red flag in the prompt:** phrasing like *"send via send_message to discord:stancsz"* is **misleading** — it's how the original job was described when it was set up, but the actual delivery uses the `deliver` config (e.g. `"deliver": "discord:1454707447402070026:1510466904450666507"`). Ignore the verb, focus on writing a good final response.

## 2. Paths

| What | Path | Gotcha |
|---|---|---|
| `HOME` | `/opt/data/home` | **NOT** `/opt/hermes` despite the CWD. The `~` in cron prompt strings is misleading. |
| Output dir | `/opt/data/home/.cron/output/<job-id>/` | Job id is the same as the cron job's `id` field (e.g. `f2f177230acb`). |
| Job config | `/opt/data/cron/jobs.json` | Inspect this to find the real `deliver` target, schedule, last status, repeat count. |
| AgenticTendies venv | `/opt/data/agentictendies/.venv/bin/python` | **Absolute path required.** `.venv/bin/python` at CWD doesn't exist. |
| Current user | `hermes` (uid 1000) | Can write to `/opt/data/home/` but **not** to `/opt/hermes/` (root-owned). |

## 3. Tooling pitfalls

- **Partial reports pollute the output dir.** If you re-run during debugging, delete the failed/empty `.md` files so only the final successful report remains. Each cron tick overwrites — leave the directory clean.
- **Re-run a working script directly:** `/opt/data/agentictendies/.venv/bin/python /opt/data/home/.cron/output/<job-id>/_run_research.py`. No need to copy scripts into a `scripts/` dir.
- **JSON dump for downstream tooling:** alongside the `.md`, write `_latest.json` with structured results. Cheap to produce, useful for the next iteration.
- **External APIs may have wrapped responses.** Don't trust your prompt's example — always probe the actual JSON shape once. See `references/quantdinger-api.md` for one worked example.

## 4. Verbosity / format

These run on tight cadences (15min–hourly, sometimes 5min). The user gets a Discord DM on every tick.

- **Ranking table up top** — one row per ticker, sortable by signal strength.
- **Short Chinese commentary** per ticker with a clear emoji (🟢/🔴/⬆️/📈) and one-line reason.
- **No lengthy prose**, no "I will now analyze…" preamble, no recap of methodology.
- **Holdings section** (if a portfolio is in play) — show shares + avg cost + total cost.
- **Footer:** "Hermes Agent | <data source> · 报告已保存至 ..."

## 5. If something fails

- Don't crash silently. If a ticker errors out, mark it `数据缺失` in the table and continue.
- The cron harness tracks `last_error` / `last_status` per job — your stderr is what populates that. Print a one-line `[WARN] klines XYZ: <reason>` for every recoverable failure.
- If the entire run fails, the harness will retry on the next tick. No need to self-retry inside one run.

## 6. Common bugs in cron scripts — known to recur

These have all shown up in live cron runs; if you see a familiar symptom, the
fix is already known.

### `get_yf_ohlcv(sym, days=N)` returns None for short windows

The typical helper in `run_cron_research.py` (AgenticTendies) has a
`min_rows=20` floor:

```python
def get_yf_ohlcv(sym, days=75):
    ...
    if df.empty or len(df) < 20:
        return None
    return df
```

That's correct for **indicator math** (RSI needs ≥14 closes, SMA20 needs 20).
But it's **wrong for position lookups** — when you just want the *current*
price for a held ticker, a 5-day window is enough, and the helper will
silently return `None` → portfolio table prints empty rows, but the script
doesn't error. Always pass a relaxed `min_rows` for price-only lookups, or
use a separate helper. The patched signature is
`get_yf_ohlcv(sym, days=5, min_rows=1)`.

Symptom: signals table populated, holdings table all `N/A` or missing rows.

### QuantDinger `/price` returns `{"price": null}` for tickers it doesn't carry

Some ETFs and ADRs (e.g. `GLD`, `TSM`) come back with HTTP 200 + `code: 0`
but `data.price: null`. The market=`USETF` fallback also returns `null` for
these. **Don't** treat this as a script error — `get_qd_price()` will return
`None` and your fallback chain (yfinance) takes over. But make sure the
fallback is actually wired up; the bug is usually the silent
`except: return None` swallowing the empty result and never reaching the
yfinance branch.

Verify once at the top of debugging:
```python
import urllib.request, json, os
for sym in [...]:
    req = urllib.request.Request(f"{BASE}/api/agent/v1/price?market=USStock&symbol={sym}")
    req.add_header("Authorization", f"Bearer {os.environ['QUANTDINGER_TOKEN']}")
    print(sym, json.loads(urllib.request.urlopen(req).read()))
```

### Single-ticker data anomalies (suspicious signals)

If **one** ticker in a homogeneous group (all AI/infrastructure) suddenly
shows RSI=85+, stochastic=100, price/SMA20 ratio > 1.5x, **don't trust it** —
it's almost always a QuantDinger data anomaly (stale feed, corp action not
adjusted, or split mis-applied). Mark it with `⚠️ 数据异常` in the table and
add a one-line caveat in commentary. Don't recommend a trade on it.

Concrete example observed: `DELL` at $420.91 with SMA20=$260.00, RSI=85.1,
stoch=100, vol_ratio=5.24. The 5x volume spike + extreme RSI + price
detached from SMA20 by 60% is the signature of a feed glitch, not a real
sell signal.

## 7. See also

- `references/quantdinger-api.md` — concrete response shapes and gotchas for the QuantDinger local API (used by several cron jobs).
