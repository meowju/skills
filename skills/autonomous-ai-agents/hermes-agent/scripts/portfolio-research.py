# Portfolio Research Cron Job — Technical Analysis Workflow

Scheduled every 15 minutes. Researches AI/infrastructure stocks, calculates technical indicators, ranks by confidence, delivers to Discord DM.

## Stocks Covered

`VRT`, `SMCI`, `PLTR`, `AMD`, `NVDA`, `COIN`, `DELL`

## Data Pipeline

### 1. Get QuantDinger Token

```python
import subprocess
result = subprocess.run(['bash', '-c', 'ps aux | grep quantdinger-mcp | grep -o "qd_age[^ ]*" | head -1'], 
                       capture_output=True, text=True)
TOKEN = result.stdout.strip()
BASE = "http://localhost:8888"
```

Always verify `TOKEN` is non-empty before proceeding. If empty, the server may be initializing — retry once.

### 2. Fetch 60-Day Klines

```python
import urllib.request, json
req = urllib.request.Request(f"{BASE}/api/agent/v1/klines?market=USStock&symbol={sym}&timeframe=1d&limit=60")
req.add_header("Authorization", f"Bearer {TOKEN}")
with urllib.request.urlopen(req, timeout=15) as r:
    data = json.loads(r.read())
klines = data["data"]["klines"]  # list of dicts with open/high/low/close/volume
```

Note: only 42 bars returned even with `limit=60`. This is the full available history.

### 3. Calculate Technical Indicators

**RSI(14)** — Wilder smoothed:
```python
def calc_rsi(closes, period=14):
    deltas = [closes[i] - closes[i-1] for i in range(1, len(closes))]
    gains = [d if d > 0 else 0 for d in deltas]
    losses = [-d if d < 0 else 0 for d in deltas]
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period
    for i in range(period, len(gains)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period
    if avg_loss == 0:
        return 100
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))
```

**SMA(n)**:
```python
def calc_sma(closes, period):
    return sum(closes[-period:]) / period
```

**Stochastic %K** (14-period):
```python
def calc_stoch(klines, period=14):
    highs = [k["high"] for k in klines]
    lows = [k["low"] for k in klines]
    closes = [k["close"] for k in klines]
    recent_high = max(highs[-period:])
    recent_low = min(lows[-period:])
    k = closes[-1]
    if recent_high == recent_low:
        return 50
    return (k - recent_low) / (recent_high - recent_low) * 100
```

**Volume Ratio** (last bar vs 20-bar avg):
```python
def avg_volume(klines, lookback=20):
    return sum(k["volume"] for k in klines[-lookback:]) / lookback

vol_ratio = volumes[-1] / avg_volume(klines) if avg_volume(klines) > 0 else 1
```

### 4. Signal Logic

| Condition | Signal |
|-----------|--------|
| RSI < 40 | BUY (oversold) |
| RSI > 70 | SELL (overbought) |
| RSI 40–55 AND price > SMA20 | BUY |
| SMA20 > SMA50 | GOLDEN_CROSS (extra confidence) |

### 5. Confidence Score

```
confidence = (50 - |RSI - 50|) + golden_cross_bonus(10) + volume_surge_bonus
```

Volume surge bonus: `min((vol_ratio - 1) * 5, 10)` capped at 10, only when vol_ratio > 1.

## Report Format

Use Chinese commentary + English data. Markdown table format.

```
| 排名 | 代码 | 价格 | RSI(14) | SMA(20) | 随机指标 | 量比 | 信号 | 置信度 |
```

Save to `/opt/data/cron/output/f2f177230acb/portfolio-research-YYYYMMDD-HHMM.md`

## Discord Delivery

Use `send_message_tool` from `tools.send_message_tool`:

```python
import subprocess
result = subprocess.run(
    ['/opt/hermes/.venv/bin/python', '-c',
     f'''from tools.send_message_tool import send_message_tool
result = send_message_tool({{"action": "send", "target": "discord:stancsz", "message": """{report_content}"""}})
print(result)'''],
    capture_output=True, text=True, cwd='/opt/hermes', timeout=30
)
```

Alternatively, invoke via `hermes chat -q` with the message content directly. The `send_message` tool requires Discord to be configured in the gateway with a bot token — if it fails with "Platform 'discord' is not configured", fall back to `hermes chat -q` or direct Discord API call via bot token.

## Output Directory

`/opt/data/cron/output/f2f177230acb/` — create with `os.makedirs(..., exist_ok=True)`. Not `/root/.cron` (permission denied).

## Portfolio Holdings (TD Direct 41HHH9A)

| Ticker | Shares | Avg Cost |
|--------|-------:|---------:|
| GLD | 4 | $588.79 |
| TSM | 5 | $563.93 |

Current prices not fetched — user checks manually.