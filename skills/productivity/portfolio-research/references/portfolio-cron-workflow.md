# Portfolio Research Cron — Technical Reference

## Cron Output Location
```
/opt/data/home/cron/output/portfolio-research-YYYYMMDD-HHMM.md
```

> Verify with `python -c "import os; print(os.path.expanduser('~/./cron/output/'))"` — HOME in WSL cron context is `/opt/data/home`, not `/opt/hermes`.

## Market Regime Detection Pattern
```python
spy = closes['SPY']
spy_sma200 = calculate_sma(spy, 200).iloc[-1]
spy_sma50  = calculate_sma(spy, 50).iloc[-1]
spy_price  = spy.iloc[-1]

if spy_price > spy_sma200:
    market_regime = "BULL"
elif spy_price > spy_sma200 * 0.97:   # 3% cushion = NEUTRAL
    market_regime = "NEUTRAL"
else:
    market_regime = "BEAR"
```
- BULL → favor SMACrossover, DualMomentum (trend-following)
- BEAR → favor RSIReversion, BollingerReversion (mean-reversion)

## MultiIndex yfinance Pattern — Dict-of-Dicts (CRITICAL)

The batch download returns a MultiIndex DataFrame: `('Close','AMD'), ('High','AMD'), ...`.
**Do NOT try to work with this as a flat MultiIndex DataFrame** — accessing `.iloc[-1]` on a MultiIndex column returns a tuple, causing `ValueError: truth value of a Series is ambiguous` in downstream indicator code. Instead, restructure into a **dict-of-dicts** on fetch.

```python
import yfinance as yf
import pandas as pd

def fetch_prices(tickers, start='2021-01-01'):
    """Returns dict: {ticker: {'close': Series, 'high': Series, 'low': Series, 'volume': Series}}"""
    data = yf.download(tickers, start=start, progress=False, auto_adjust=True)
    result = {}
    if isinstance(data.columns, pd.MultiIndex):
        tickers_found = data.columns.get_level_values(1).unique()
        for col in tickers_found:
            result[col] = {}
            for attr in ['Close', 'High', 'Low', 'Volume']:
                try:
                    result[col][attr.lower()] = data[(attr, col)].squeeze().dropna()
                except Exception:
                    result[col][attr.lower()] = data[(attr, col)].squeeze()
        return result
    else:
        # Single ticker, no MultiIndex
        close = data['Close'].squeeze() if 'Close' in data.columns else data.squeeze()
        result[tickers[0]] = {
            'close': close,
            'high': data.get('High', close).squeeze(),
            'low': data.get('Low', close).squeeze(),
            'volume': data.get('Volume', close).squeeze()
        }
        return result

# Usage:
prices = fetch_prices(['VRT', 'SPY', 'GLD'], start='2021-01-01')
close = prices['VRT']['close']      # pd.Series
high  = prices['VRT']['high']        # pd.Series (for ATR)
low   = prices['VRT']['low']        # pd.Series (for ATR)
vol   = prices['VRT']['volume']     # pd.Series
```

**⚠️ Common mistake to avoid:** Calling `calc_atr(close, close, close, 14)` — ATR requires real OHLC data. Passing the same Series three times produces `ATR=0` and breaks stop/target levels. Always pass `high=high_series, low=low_series, close=close_series`.

**⚠️ Accessing SPY/VIX from dict:** `spy_price = prices_raw.get('SPY', {}).get('close', prices_raw.get('SPY'))` — `prices_raw['SPY']` is a dict, not a Series directly. For VIX: `v = vix_raw['^VIX']; vix = v.get('close', v) if isinstance(v, dict) else v`.

## VIX Fetch (Must Be Separate Call)
```python
vix_raw = fetch_prices(['^VIX'], start='2021-01-01')
vix = None
if vix_raw and '^VIX' in vix_raw:
    v = vix_raw['^VIX']
    vix = v.get('close', v) if isinstance(v, dict) else v
vix_val = float(vix.iloc[-1]) if vix is not None and not pd.isna(vix.iloc[-1]) else 20.0
```

## MultiIndex Error Symptoms
- `ValueError: truth value of a Series is ambiguous` → MultiIndex column accessed with `.iloc[-1]` — restructure via dict-of-dicts above
- `SMA50=$0` or `ATR14=$0` → called `calc_atr(s, s, s, 14)` instead of `calc_atr(high, low, close, 14)`

## MACD Histogram Manual Computation
```python
def compute_macd(prices, fast=12, slow=26, signal=9):
    ema_fast = prices.ewm(span=fast, adjust=False).mean()
    ema_slow = prices.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram

macd_line, signal_line, hist = compute_macd(s)
macd_hist = hist.iloc[-1]          # Latest histogram value (float, NOT a Series)
macd_dir  = 'BULL' if macd_hist > 0 else 'BEAR'
```
- A **positive histogram** (>0) = MACD above signal line = bullish momentum
- `hist.iloc[-1]` gives float. Do NOT use `hist[-1]` (Series indexing returns float, okay but ambiguous — `.iloc[-1]` is explicit).

## Combined Signal Logic
```python
buy_count = sum([1 for sig in [sma_signal, rsi_signal, macd_signal] 
                 if sig in ("BULLISH", "BUY")])
sell_count = sum([1 for sig in [sma_signal, rsi_signal, macd_signal] 
                  if sig in ("BEARISH", "SELL")])

if buy_count >= 2:
    overall = "BUY";   confidence = int((buy_count/3)*100 + (100-rsi)/3)
elif sell_count >= 2:
    overall = "SELL";  confidence = int((sell_count/3)*100 + (rsi-50)/3)
else:
    overall = "HOLD";  confidence = 50

confidence = min(95, max(30, confidence))
```

## Entry/Stop/Target from ATR
```python
atr = calculate_atr(high, low, close_series, 14).iloc[-1]
stop_loss = price - 2.0 * atr       # 2x ATR stop
take_profit = price + 3.5 * atr     # 3.5x ATR target
```

## Walk-Forward + Monte Carlo Full Pipeline
```python
from agentictendies.backtester.walk_forward import run_walk_forward
from agentictendies.backtester.monte_carlo import run_monte_carlo

# Walk-forward (SMACrossover only)
wf_rets, wf_eq, wf_log = run_walk_forward(s, train_len=252, test_len=126)
wf_sharpe = (wf_rets.mean() / wf_rets.std()) * np.sqrt(252) if wf_rets.std() > 0 else 0.0

# Monte Carlo
rets = s.pct_change().dropna()
mc = run_monte_carlo(rets, starting_capital=100000.0, num_paths=1000, horizon_days=252)
# Returns: {'Starting Capital', 'Median Final Capital', '95% VaR', '99% VaR', 'Prob of Ruin'}
var95 = mc.get('95% VaR', 'N/A')
```

## Volume Ratio
```python
vol = data['Volume'][ticker].ffill().bfill()
vol_20avg = vol.rolling(20).mean().iloc[-1]
vol_ratio = vol.iloc[-1] / vol_20avg if vol_20avg > 0 else 1.0
# vol_ratio > 1.5 = unusual volume, > 2.0 = significant volume spike
```

## SPY + VIX in Same Fetch
```python
# VIX (^VIX) is a separate download — can't batch with equities in same call
all_symbols = CANDIDATES + BENCHMARKS  # no ^VIX here
data = yf.download(all_symbols, ...)
closes = data['Close']

# VIX separately
vix = yf.download('^VIX', start=TODAY, end=TODAY, progress=False)
vix_price = float(vix['Close'].iloc[-1]) if not vix.empty else None
```

## Output Cron Filename
```python
import datetime
ts = datetime.datetime.now().strftime('%Y%m%d-%H%M')
filename = f"/opt/data/cron/output/portfolio-research-{ts}.md"
```

## Key Metrics to Report
- RSI(14), SMA(50), SMA(200), ATR(14), MACD histogram, Volume ratio (20d)
- WFA OOS Sharpe, stop-loss, take-profit, entry price, confidence
- Portfolio: current price, RSI, MACD hist, PnL %, volume ratio, alerts
