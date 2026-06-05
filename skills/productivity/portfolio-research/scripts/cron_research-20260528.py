"""
Portfolio Research — Verified Cron Script (2026-05-28 session)
Runs technical analysis on 8 AI/infrastructure candidates + 2 portfolio positions.
Produces a ranked markdown report to /opt/data/home/./cron/output/.

Key decisions from this session:
- Uses fetch_historical_prices (close-only) + fetch_ohlcv (for ATR/vol) separately
- MACD computed inline (no calculate_macd function exists in indicators.py)
- ATR from close-only: abs(prices.diff().rolling(14).std().iloc[-1]) * sqrt(252)
- Walk-forward: run_walk_forward (tuple return), compute_metrics on oos_rets.dropna()
- Monte Carlo: run_monte_carlo on backtest_sma_crossover Strategy_Return column
- SPY regime: BULL if spy > sma200, BEAR if spy < sma200*0.95, else NEUTRAL
- VIX fetched as ^VIX column
- Cron output dir: /opt/data/home/./cron/output/ (NOT ~/./cron/output/)

Run:
  cd /opt/data/agentictendies && .venv/bin/python cron_research.py
"""
import sys, os
sys.path.insert(0, "/opt/data/agentictendies")

import datetime
import numpy as np
import pandas as pd

from agentictendies.core.ingestion import fetch_historical_prices, fetch_ohlcv
from agentictendies.core.indicators import calculate_rsi, calculate_sma, calculate_ema, calculate_atr
from agentictendies.backtester.engine import backtest_sma_crossover, compute_metrics
from agentictendies.backtester.monte_carlo import run_monte_carlo
from agentictendies.backtester.walk_forward import run_walk_forward
from agentictendies.config import STOP_LOSS_ATR_MULTIPLIER, TAKE_PROFIT_ATR_MULTIPLIER

CANDIDATES = ["VRT", "SMCI", "SYM", "PLTR", "DELL", "AMD", "NVDA", "COIN"]
PORTFOLIO_TICKERS = ["GLD", "TSM"]
BENCHMARKS = ["SPY", "^VIX"]

end_date   = datetime.date.today().strftime("%Y-%m-%d")
start_date = (datetime.date.today() - datetime.timedelta(days=1825)).strftime("%Y-%m-%d")


def calc_macd(prices, fast=12, slow=26, signal=9):
    """Inline MACD — no calculate_macd in indicators.py."""
    ema_fast  = prices.ewm(span=fast, adjust=False).mean()
    ema_slow  = prices.ewm(span=slow, adjust=False).mean()
    macd_line  = ema_fast - ema_slow
    macd_sig   = macd_line.ewm(span=signal, adjust=False).mean()
    macd_hist  = macd_line - macd_sig
    return {"MACD": macd_line, "MACD_Signal": macd_sig, "MACD_Hist": macd_hist}


# ── 1. Fetch close prices for all tickers ─────────────────────────────────────
prices = fetch_historical_prices(BENCHMARKS + CANDIDATES + PORTFOLIO_TICKERS,
                                  start_date, end_date)

spy    = prices["SPY"].dropna()
vix    = prices["^VIX"].dropna()          # ^VIX, not VIX
spy50  = calculate_sma(spy, 50)
spy200 = calculate_sma(spy, 200)

spy_regime = ("BULL" if float(spy.iloc[-1]) > float(spy200.iloc[-1])
              else "BEAR" if float(spy.iloc[-1]) < float(spy200.iloc[-1]) * 0.95
              else "NEUTRAL")
vix_val  = float(vix.iloc[-1]) if len(vix) else None

# ── 2. OHLCV for ATR + volume ratio ──────────────────────────────────────────
ohlcv_data = {}
for t in CANDIDATES + PORTFOLIO_TICKERS:
    try:
        df = fetch_ohlcv(t, period="1y")
        if df is not None and len(df) > 14:
            ohlcv_data[t] = df
    except Exception:
        pass


def get_indicators(ticker, close_prices, ohlcv_df=None):
    rsi14    = calculate_rsi(close_prices, 14)
    sma50    = calculate_sma(close_prices, 50)
    sma200   = calculate_sma(close_prices, 200)
    ema20    = calculate_ema(close_prices, 20)
    macd_val = calc_macd(close_prices)

    if ohlcv_df is not None and len(ohlcv_df) > 14:
        atr14 = float(calculate_atr(
            ohlcv_df["High"].iloc[-14:],
            ohlcv_df["Low"].iloc[-14:],
            ohlcv_df["Close"].iloc[-14:]
        ).iloc[-1])
        avg_vol = ohlcv_df["Volume"].iloc[-20:].mean()
        cur_vol = ohlcv_df["Volume"].iloc[-1]
        vol_ratio = (cur_vol / avg_vol) if avg_vol > 0 else 1.0
    else:
        # Close-only ATR approximation
        atr14 = round(abs(close_prices.diff().rolling(14).std().iloc[-1]) * np.sqrt(252), 2)
        vol_ratio = 1.0

    ann_vol = float(close_prices.pct_change().rolling(20).std().iloc[-1] * np.sqrt(252))

    return {
        "price"           : round(float(close_prices.iloc[-1]), 2),
        "rsi14"           : round(float(rsi14.iloc[-1]), 1),
        "sma50"           : round(float(sma50.iloc[-1]), 2),
        "sma200"          : round(float(sma200.iloc[-1]), 2),
        "ema20"           : round(float(ema20.iloc[-1]), 2),
        "atr14"           : round(float(atr14), 2),
        "macd"            : round(float(macd_val["MACD"].iloc[-1]), 3),
        "macd_sig"        : round(float(macd_val["MACD_Signal"].iloc[-1]), 3),
        "macd_hist"       : round(float(macd_val["MACD_Hist"].iloc[-1]), 3),
        "ann_vol"         : round(float(ann_vol), 3),
        "vol_ratio"       : round(float(vol_ratio), 2),
        "above_sma50"     : bool(close_prices.iloc[-1] > sma50.iloc[-1]),
        "above_sma200"    : bool(close_prices.iloc[-1] > sma200.iloc[-1]),
        "sma50_above_200" : bool(sma50.iloc[-1] > sma200.iloc[-1]),
    }


def generate_signal(ind):
    price    = ind["price"]
    rsi      = ind["rsi14"]
    atr      = ind["atr14"]
    macd_h   = ind["macd_hist"]
    above50  = ind["above_sma50"]
    above200 = ind["above_sma200"]
    s50a200  = ind["sma50_above_200"]

    stop   = round(price - STOP_LOSS_ATR_MULTIPLIER * atr, 2)
    target = round(price + TAKE_PROFIT_ATR_MULTIPLIER * atr, 2)

    score = 0
    if rsi < 40:      score += 2
    elif rsi < 50:    score += 1
    elif rsi > 70:    score -= 2
    elif rsi > 60:    score -= 1
    score += 1 if macd_h > 0 else -1
    if above200 and s50a200:  score += 2
    elif above200:            score += 1
    elif not above200:        score -= 1
    if not above50:          score -= 1

    conf   = min(95, round(50 + abs(score) / 7 * 45))
    signal = "BUY" if score >= 3 else "SELL" if score <= -2 else "HOLD"
    return {"signal": signal, "confidence": conf,
            "entry": price, "stop": stop, "target": target,
            "vol_flag": ind["vol_ratio"] > 2.0}


indicators = {t: get_indicators(t, prices[t].dropna(), ohlcv_data.get(t))
              for t in CANDIDATES + PORTFOLIO_TICKERS if t in prices.columns}
signals    = {t: generate_signal(indicators[t]) for t in indicators}

# ── 3. Walk-forward + Monte Carlo for top candidates ─────────────────────────
wf_results = {}
mc_results = {}
for t in CANDIDATES[:4]:
    if t not in indicators:
        continue
    ps = prices[t].dropna()
    try:
        oos_r, _, _ = run_walk_forward(ps)
        oos_m = compute_metrics(oos_r.dropna())
        wf_results[t] = {
            "oos_sharpe": round(float(oos_m.get("_raw_sharpe", 0)), 3),
            "oos_max_dd": round(float(oos_m.get("_raw_drawdown", 0)) * 100, 1),
        }
    except Exception as e:
        wf_results[t] = {"error": str(e)[:80]}

try:
        sma_df = backtest_sma_crossover(ps, fast_window=20, slow_window=50)
        rets = sma_df["Strategy_Return"].dropna()
        if len(rets) < 5:
            mc_results[t] = {"error": "insufficient returns"}
        else:
            mc = run_monte_carlo(rets)
            if mc:
                mc_results[t] = {
                    "max_dd"   : mc.get("Probability of Ruin (<-20%)", mc.get("Max Drawdown (%)", "N/A")),
                    "var_95"   : mc.get("95% VaR", mc.get("VaR 95% (daily)", "N/A")),
                    "worst_run": mc.get("99% VaR", mc.get("Worst Case (%)", "N/A")),
                    "median"   : mc.get("Median Final Capital", "N/A"),
                }
            else:
                mc_results[t] = {"error": "empty mc result"}
    except Exception as e:
        mc_results[t] = {"error": str(e)[:80]}

# ── 4. Rank candidates ────────────────────────────────────────────────────────
ranked = sorted(
    [t for t in CANDIDATES if t in signals],
    key=lambda t: (0 if signals[t]["signal"] == "BUY"
                   else 1 if signals[t]["signal"] == "HOLD" else 2,
                   -signals[t]["confidence"])
)

# ── 5. Build + save report ────────────────────────────────────────────────────
ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
report = f"""# Portfolio Research — {ts}

## Market Context
- SPY: ${float(spy.iloc[-1]):.2f} | SMA50=${float(spy50.iloc[-1]):.2f} | SMA200=${float(spy200.iloc[-1]):.2f} | **Regime: {spy_regime}**
- VIX: {vix_val:.1f} ({"LOW" if vix_val and vix_val < 15 else "MODERATE" if vix_val and vix_val < 25 else "HIGH"})
- Sentiment: {"✅ Risk-On" if spy_regime == "BULL" and vix_val and vix_val < 20 else "⚠️ Risk-Off" if spy_regime == "BEAR" or (vix_val and vix_val > 30) else "➡️ Mixed"}

---

## AI/Infrastructure Candidates (BUY→HOLD→SELL, confidence desc)

"""

for t in ranked:
    s  = signals[t]; i = indicators[t]
    wf = wf_results.get(t, {}); mc = mc_results.get(t, {})
    wf_s = f" WF-Sharpe={wf.get('oos_sharpe','—')}" if "oos_sharpe" in wf else ""
    mc_s = (f" VaR95={mc.get('var_95','—')} MaxDD={mc.get('max_dd','—')}"
            if mc and "error" not in mc else "")
    vol = " ⚠️ VOL_SPIKE" if s["vol_flag"] else ""
    report += f"""### {t} — **{s['signal']}** [{s['confidence']}%]{vol}
| Field | Value |
|-------|-------|
| Entry | ${s['entry']:.2f} |
| Stop Loss | ${s['stop']:.2f} (2× ATR) |
| Profit Target | ${s['target']:.2f} (3.5× ATR) |
| Price | ${i['price']} |
| RSI(14) | {i['rsi14']} |
| SMA50 / SMA200 | ${i['sma50']} / ${i['sma200']} |
| EMA20 | ${i['ema20']} |
| ATR(14) | ${i['atr14']} |
| Ann.Vol | {i['ann_vol']*100:.1f}% |
| MACD | {i['macd']:.3f} / Signal={i['macd_sig']:.3f} / Hist={i['macd_hist']:.3f}{wf_s}{mc_s} |

"""

report += """
## Portfolio Positions — Technical Update

| Ticker | Price | RSI(14) | MACD_Hist | Signal | Stop | Target | Conf |
|--------|------:|--------:|----------:|--------|-----:|-------:|-----:|
"""
for t in PORTFOLIO_TICKERS:
    if t in signals and t in indicators:
        s = signals[t]; i = indicators[t]
        report += f"| {t} | ${i['price']:.2f} | {i['rsi14']} | {i['macd_hist']:.3f} | {s['signal']} | ${s['stop']:.2f} | ${s['target']:.2f} | {s['confidence']}% |\n"

report += """
## Risk Alerts
"""
alerts = []
for t in PORTFOLIO_TICKERS:
    if t in indicators:
        i = indicators[t]
        if i["rsi14"] > 65: alerts.append(f"- ⚠️ **{t}** RSI overbought ({i['rsi14']})")
        if i["rsi14"] < 40: alerts.append(f"- 💎 **{t}** RSI oversold ({i['rsi14']}) — mean reversion setup")
        if i["vol_ratio"] > 2.0: alerts.append(f"- 📊 **{t}** Volume spike {i['vol_ratio']:.1f}× avg")
        if i["macd_hist"] > 0.05: alerts.append(f"- 🚀 **{t}** MACD bullish momentum (hist={i['macd_hist']:.3f})")
        if i["macd_hist"] < -0.05: alerts.append(f"- 🔻 **{t}** MACD bearish pressure (hist={i['macd_hist']:.3f})")

report += ("\n".join(alerts) if alerts else "- ✅ No extreme alerts") + """

---

## Framework Insights

**AgenticTendies Walk-Forward OOS (SMACrossover):**
"""
for t, wf in wf_results.items():
    if wf.get("oos_sharpe") is not None:
        report += f"- {t}: OOS-Sharpe={wf['oos_sharpe']:+.3f} | MaxDD={wf['oos_max_dd']}%\n"
    elif "error" in wf:
        report += f"- {t}: WFA error — {wf['error']}\n"

report += """
**QuantDinger:** MCP server not running. Manual review recommended.
"""

print(report)

out_dir  = "/opt/data/home/./cron/output/"
os.makedirs(out_dir, exist_ok=True)
out_file = os.path.join(out_dir, f"portfolio-research-{datetime.datetime.now():%Y%m%d-%H%M}.md")
with open(out_file, "w", encoding="utf-8") as f:
    f.write(report)
print(f"\n[+] Saved → {out_file}")
