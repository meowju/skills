# Compute Indicators Patterns (May 2026 Session)

## Quick Reference — All Indicators

```python
from agentictendies.core.indicators import (
    calculate_rsi,    # window=14 default, returns pd.Series(0-100)
    calculate_sma,    # rolling mean, window=N required
    calculate_ema,    # exponential moving average, span=N required
    calculate_atr,    # needs (high, low, close), returns pd.Series
)
import numpy as np

# In a loop over tickers:
s = close_prices[ticker].dropna()
h = high_df[ticker].dropna()
l = low_df[ticker].dropna()

rsi   = calculate_rsi(s)
sma20 = calculate_sma(s, 20)
sma50 = calculate_sma(s, 50)
sma200 = calculate_sma(s, 200)
atr   = calculate_atr(h, l, s)          # uses high/low/close
```

---

## RSI (14) — Interpretation Levels

| RSI Value | Zone | Action |
|-----------|------|--------|
| RSI > 70 | Overbought | SELL/REDUCE signal; do NOT buy |
| RSI 60-70 | Bullish but warming | HOLD existing; no new BUY |
| RSI 45-60 | Neutral | HOLD, watch for setups |
| RSI 40-45 | Bearish-leaning | Possible mean reversion candidate |
| RSI < 40 | Oversold | BUY candidate (mean reversion thesis) |
| RSI < 30 | Deep oversold | STRONG BUY if MACD confirms |

---

## MACD (12, 26, 9) — Full Computation

```python
ema12  = calculate_ema(s, 12)
ema26  = calculate_ema(s, 26)
macd_line = ema12 - ema26
sig_line  = calculate_ema(macd_line.fillna(0), 9)
histogram = macd_line - sig_line          # hist > 0 → bullish

# Current values:
macd_cur   = macd_line.iloc[-1]
sig_cur    = sig_line.iloc[-1]
hist_cur   = histogram.iloc[-1]
hist_prev  = histogram.iloc[-2]

# Direction
macd_dir = 'BULL' if macd_cur > sig_cur else 'BEAR'

# FLIP detection (new crossover this period)
macd_flip = 1 if (hist_cur > 0 and hist_prev < 0) else (
           -1 if (hist_cur < 0 and hist_prev > 0) else 0)
#  1 = bullish crossover, -1 = bearish crossover, 0 = no change
```

---

## Distance to 200-SMA (Trend Signal)

```python
sma200_val = sma200.iloc[-1]
cur_price  = s.iloc[-1]
dist_sma200 = (cur_price / sma200_val - 1) * 100  # percentage

# Interpretation:
#   dist > 0  → price above SMA200 (bullish)
#   dist < -15% → price far below SMA200 (weakness, avoid)
#   dist < -15% + RSI < 40 → oversold bounce candidate
#   dist > +50% → price extended (overbought risk)
```

---

## ATR (14) — Position Sizing and Stops

```python
atr_val = atr.iloc[-1]

# Stop loss = entry - 2×ATR
# Take profit = entry + 3.5×ATR  (from agentictendies config)
# Kelly fraction: kelly = (win_rate * avg_win - avg_loss) / avg_win  (simplified)

# For Monte Carlo risk: annual_vol = s.pct_change().rolling(20).std().iloc[-1] * np.sqrt(252)
ann_vol = s.pct_change().rolling(20).std().iloc[-1] * np.sqrt(252)
```

---

## Walk-Forward OOS Validation (Rolling Windows)

```python
# Pattern: train on last N days, test on next M days, slide forward
def run_wf_bt(ticker_close, strat_fn, train_len=252, oos_len=30):
    """Rolling OOS backtest using in-sample training window."""
    n = len(ticker_close)
    train_end = n - oos_len
    train = ticker_close.iloc[:train_end]
    test  = ticker_close.iloc[train_end:]
    
    # In-sample optimization: train the strategy
    train_bt  = strat_fn(train)
    train_rets = train_bt['Strategy_Return'].dropna()
    wf_sharpe = (train_rets.mean() / train_rets.std()) * np.sqrt(252) if len(train_rets) > 30 else 0
    
    # Out-of-sample test — prepend warmup for MA indicators
    warmup     = ticker_close.iloc[max(0, train_end-200):train_end]
    extended   = pd.concat([warmup, test])
    oos_bt     = strat_fn(extended)
    oos_rets   = oos_bt['Strategy_Return'].iloc[-len(test):].dropna()
    oos_sharpe = (oos_rets.mean() / oos_rets.std()) * np.sqrt(252) if len(oos_rets) > 10 else 0
    
    return wf_sharpe, oos_sharpe

# Use oos_sharpe > 0 and oos_sharpe >= wf_sharpe * 0.5 as quality gate
```

---

## Monte Carlo Portfolio Return CI

```python
import numpy as np

def monte_carlo_30d(portfolio_rets_list, n_sim=1000, horizon=30):
    """
    portfolio_rets_list: list of pd.Series (daily returns per ticker).
    Equal-weight portfolio.
    Returns 5th/50th/95th percentile of final capital multiplier.
    """
    # Align to common length (trim to shortest)
    min_len = min(len(r) for r in portfolio_rets_list)
    aligned = [r.iloc[-min_len:] for r in portfolio_rets_list]
    combined = pd.concat(aligned, axis=1).mean(axis=1)  # equal-weight

    finals = []
    for _ in range(n_sim):
        idx = np.random.randint(0, len(combined), horizon)
        path = (1 + combined.iloc[idx].values).cumprod()
        finals.append(path[-1] if len(path) > 0 else 1.0)

    finals = np.array(finals)
    return np.percentile(finals, 5), np.median(finals), np.percentile(finals, 95)
```

---

## Volatility (20-day Rolling)

```python
ret20_std = s.pct_change().rolling(20).std().iloc[-1]
ann_vol   = ret20_std * np.sqrt(252)
```

---

## All in One: Per-Ticker Indicator Data Collection

```python
def get_all_indicators(ticker, close_prices, high_df, low_df, vol_df):
    s = close_prices[ticker].dropna()
    h = high_df[ticker].dropna()
    l = low_df[ticker].dropna()
    v = vol_df[ticker].dropna()

    rsi     = calculate_rsi(s)
    ema12   = calculate_ema(s, 12)
    ema26   = calculate_ema(s, 26)
    macd_l  = ema12 - ema26
    sig_l   = calculate_ema(macd_l.fillna(0), 9)
    hist    = macd_l - sig_l
    sma20   = calculate_sma(s, 20)
    sma50   = calculate_sma(s, 50)
    sma200  = calculate_sma(s, 200)
    atr     = calculate_atr(h, l, s)

    cur  = s.iloc[-1]
    prev = s.iloc[-2]
    hcur = hist.iloc[-1]
    hprv = hist.iloc[-2]

    return {
        'price':       round(cur, 2),
        'day_chg':     round((cur/prev - 1)*100, 2),
        'week_chg':    round((cur/s.iloc[-6] - 1)*100, 2) if len(s) >= 6 else 0,
        'month_chg':   round((cur/s.iloc[-22] - 1)*100, 2) if len(s) >= 22 else 0,
        'rsi':         round(rsi.iloc[-1], 1),
        'macd_dir':    'BULL' if macd_l.iloc[-1] > sig_l.iloc[-1] else 'BEAR',
        'macd_hist':   round(hcur, 4),
        'macd_flip':   1 if (hcur > 0 and hprv < 0) else (-1 if (hcur < 0 and hprv > 0) else 0),
        'sma200':      round(sma200.iloc[-1], 2),
        'dist_sma200': round((cur/sma200.iloc[-1] - 1)*100, 2),
        'high52':      round(s.rolling(252).max().iloc[-1], 2),
        'low52':       round(s.rolling(252).min().iloc[-1], 2),
        'atr14':       round(atr.iloc[-1], 2),
        'vol':         int(v.iloc[-1]) if len(v) > 0 else 0,
    }
```
