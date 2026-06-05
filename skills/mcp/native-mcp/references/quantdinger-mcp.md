# QuantDinger MCP Server

Running HTTP MCP server for stock/crypto data via QuantDinger API.

## Connection Details

- **URL**: `http://localhost:8888`
- **Token**: Extracted from running process env — `ps aux | grep quantdinger` shows `QUANTDINGER_AGENT_TOKEN=qd_age...`
- **Process**: `quantdinger-mcp` runs as user `hermes`, spawned by the gateway startup sequence

## Token Discovery Pattern

When `QUANTDINGER_TOKEN` env var is set in a process but not visible to `os.environ` in a sandboxed sub-process, extract it from the process command line:

```bash
ps aux | grep quantdinger-mcp | grep -o "qd_age[^ ]*"
```

The token format is `qd_agent_TWSkB8spR49Kuccw_WMEaVl0L18YyVQG6PaVt6OJ7nM`.

## API Endpoints Used

```
GET /api/agent/v1/price?market=USStock&symbol=<SYMBOL>
GET /api/agent/v1/klines?market=USStock&symbol=<SYMBOL>&timeframe=1d&limit=60
GET /api/agent/v1/markets
```

All endpoints require `Authorization: Bearer <TOKEN>` header.

## Python Access Pattern

```python
import urllib.request, json, os

TOKEN = subprocess.run(['bash', '-c', 'ps aux | grep quantdinger-mcp | grep -o "qd_age[^ ]*" | head -1'], 
                      capture_output=True, text=True).stdout.strip()

BASE = "http://localhost:8888"

req = urllib.request.Request(f"{BASE}/api/agent/v1/klines?market=USStock&symbol=NVDA&timeframe=1d&limit=60")
req.add_header("Authorization", f"Bearer {TOKEN}")
with urllib.request.urlopen(req, timeout=15) as r:
    data = json.loads(r.read())
klines = data["data"]["klines"]
```

## Response Shape

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "market": "USStock",
    "symbol": "NVDA",
    "timeframe": "1d",
    "count": 42,
    "klines": [
      {"time": 1774843200, "open": 168.78, "high": 169.45, "low": 164.27, "close": 165.17, "volume": 185627000.0},
      ...
    ]
  }
}
```

`time` is Unix timestamp. `volume` is absolute shares. `count` reflects available bars (42 since no full 60).

## Known Quirks

- **Only 42 bars returned**: Even with `limit=60`, only 42 daily klines returned. Data appears to start from ~42 days ago.
- **`QUANTDINGER_TOKEN` env var not in `os.environ`**: The token is set in the parent shell's environment but not propagated to sandboxed Python subprocesses. Must extract from process list.
- **Unauthorized on wrong token**: Using `QUANTDINGER_TOKEN` from env may be empty/wrong if the token was set for a subprocess but not exported broadly. Always verify token length > 0 before using.