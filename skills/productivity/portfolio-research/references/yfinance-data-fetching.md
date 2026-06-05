# yfinance Data Fetching — Reference Patterns (May 2026)

## The Core Problem
yfinance 1.4.0+ has a broken/changed API: most tickers no longer return `Adj Close` — only `Close`. Batch downloads return MultiIndex columns `('Close', ticker)` instead of a simple DataFrame. Getting this wrong produces `KeyError: 'Adj Close'` on BABA/TSM/GLD/TLT and similar.

---

## Correct Fetching Pattern

```python
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

# Always use auto_adjust=True to get consistent Close column (no Adj Close ambiguity)
raw = yf.download(
    ['BABA', 'TSM', 'GLD', 'TLT', 'MU', 'SPY'],
    start=start,
    end=end,
    progress=False
    # auto_adjust=True  # NOT needed if using raw['Close'] below
)
```

### Extracting Price Data from MultiIndex Results

```python
# If raw.columns is MultiIndex like [('Close', 'BABA'), ('High', 'BABA'), ...]
close_prices = raw['Close'].copy()          # pd.DataFrame: index=dates, cols=tickers
high_df      = raw['High'].copy()
low_df       = raw['Low'].copy()
vol_df       = raw['Volume'].copy()

# Individual ticker:
#   close_prices['BABA']  ← returns pd.Series (dates → close)
#   close_prices['BABA'].iloc[-1]  ← last close price
#
# WRONG patterns that will fail:
#   raw['Close']['BABA']    ← KeyError (MultiIndex doesn't slice like this)
#   raw['Adj Close']['BABA'] ← 'Adj Close' often not present
#   raw.loc[:, 'Close']     ← wrong for MultiIndex
```

### Single-Ticker Fetch (for earnings calendars, info dumps)

```python
t = yf.Ticker('CRSP')
info = t.info                       # dict of metadata
calendar = t.calendar              # may return None or DataFrame
earnings_date = info.get('earningsNextAnnouncementDate')
```

---

## Known Ticker Availability Edge Cases

| Ticker | Issue | Fix |
|--------|-------|-----|
| **GEV** | Starts May 2022 (542 rows for 5y), not full 1254 | Normal — GE Vernova demerged from GE in Apr 2022. Use only from its listing date. |
| **IRBT** | No data (0 rows) | iRobot acquired by Amazon ( Oct 2023). No reliable 5y history. Drop from universe. |
| **NEP** | No data (0 rows) | Nextera Energy Partners LP — possible ticker change. Drop from universe. |

```python
# Always validate after fetch:
if len(price_df) < 100:
    print(f"⚠ {ticker}: only {len(price_df)} rows — likely delisted or name change. Drop it.")
```

---

## Computing Returns and Indicators — Vectorized

```python
# Daily returns (first row will be NaN — drop it)
returns = close_prices.pct_change().dropna()

# Current price
cur = close_prices[ticker].iloc[-1]

# Day/week/month change
prev   = close_prices[ticker].iloc[-2]   # yesterday close
week   = close_prices[ticker].iloc[-6]   # ~1 week ago (5 trading days)
month  = close_prices[ticker].iloc[-22]  # ~1 month ago (22 trading days)

day_chg   = (cur / prev  - 1) * 100
week_chg  = (cur / week  - 1) * 100
month_chg = (cur / month - 1) * 100
```

---

## 52-Week High/Low

```python
high52 = close_prices[ticker].rolling(252).max().iloc[-1]
low52  = close_prices[ticker].rolling(252).min().iloc[-1]
```

---

## Mixing Ticker Dates (GEV Starts Later)

When running backtests that require aligned dates across tickers:
```python
# GEV has ~542 rows (May 2022–present) while others have 1254
# Always check: if ticker data is shorter, backtest should start from its available date
# Or reindex to common dates (careful: forward-fill breaks strategy signals)

# For mixed-length backtests, filter to shortest available history:
min_rows = min(len(close_prices[t]) for t in tickers)
aligned = close_prices.iloc[-min_rows:]
```

---

## Key Imports for This Workflow

```python
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from agentictendies.core.indicators import calculate_rsi, calculate_sma, calculate_ema, calculate_atr
```
