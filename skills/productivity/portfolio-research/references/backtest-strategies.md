# Backtest Strategy Reference

## From agentictendies — 6 Core Strategies

### 1. RSI Mean Reversion
- **Entry**: RSI(14) < 30 (oversold)
- **Exit**: RSI(14) > 50 OR stop-loss hit
- **Stop**: 2× ATR from entry
- **Take Profit**: 3.5× ATR from entry
- **Timeframe**: Daily
- **Universe**: Works best for: GLD (precious metals), TLT (bonds), large-cap mean-reverting stocks

### 2. MACD Crossover
- **Entry**: MACD line crosses above Signal line (bullish)
- **Exit**: MACD line crosses below Signal line (bearish)
- **Parameters**: Fast=12, Slow=26, Signal=9
- **Timeframe**: Daily
- **Works best for**: TSM, MU (trending semiconductor names)

### 3. Dual Momentum
- **Relative Momentum**: Long security if it beats SPY over N periods
- **Absolute Momentum**: Require security > 200-day SMA (market regime filter)
- **Exit**: Security falls below SMA OR underperforms SPY for 2 consecutive months
- **Works best for**: BABA (China/economic sensitivity + macro regime filter)

### 4. Bollinger Band Reversion
- **Entry**: Price touches lower Bollinger Band (20-day, 2σ) → mean reversion long
- **Exit**: Price returns to middle band OR upper band touched
- **Stop**: 2× ATR below entry
- **Works best for**: GLD (gold oscillates in ranges), TLT (range-bound in normal rate env)

### 5. SMA Crossover
- **Entry**: 20-day SMA crosses above 50-day SMA (golden cross)
- **Exit**: 20-day SMA crosses below 50-day SMA (death cross)
- **Timeframe**: Daily
- **Works best for**: TSM, MU — regime detection (bull/bear market filtering)

### 6. Donchian Breakout
- **Entry**: Price breaks above 20-day Donchian channel high
- **Exit**: Price closes below 20-day Donchian channel low
- **Parameters**: Lookback=20 days
- **Works best for**: Strong trends — TSM, MU in strong uptrends

## Walk-Forward Analysis
- **In-sample**: 60-day rolling window
- **Out-of-sample (OOS)**: 30-day forward test
- **Success criteria**: OOS Sharpe > 0.5, positive OOS CAGR, max OOS drawdown < 20%
- **Rule**: If OOS results are poor, discard strategy for that ticker

## Monte Carlo
- **Sims**: 1000 bootstrap resamples of trade returns
- **Output**: 5th/50th/95th percentile return range over N-day horizon
- **Alert threshold**: If 5th percentile < -10%, flag as high-risk

## Kelly Sizing
- Calculated from trade history; bounded 5–20%; halved for safety → max 10% portfolio per trade

## Per-Ticker Strategy Fit
| Ticker | Sector | Best Strategies |
|--------|--------|-----------------|
| BABA | China retail/tech | Dual Momentum, RSI Reversion |
| TSM | Semicon foundry | MACD Crossover, Donchian Breakout |
| GLD | Precious metals | RSI Reversion, Bollinger Reversion |
| TLT | US Treasuries | RSI Reversion, SMA Crossover |
| MU | Semicon memory | MACD Crossover, Donchian Breakout |
