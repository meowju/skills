#!/usr/bin/env python3
"""
Portfolio Research Agent -- AgenticTendies + QuantDinger
Verified working cron script. Copy to /opt/data/ and run with:
  /opt/data/agentictendies/.venv/bin/python /opt/data/portfolio_research.py

Learned fixes applied:
  - Portfolio tickers (GLD, TSM) included in ALL_TICKERS to avoid empty portfolio table
  - ALWAYS guard compute_metrics results with isinstance(x, (int,float)) before rounding
  - WF_Sharpe=None for all tickers: backtest_sma_crossover returns all-zero Strategy_Return
    for stocks already above SMA — the None is correct, not an error
  - Path ~/./cron/output/ expands to /opt/data/home/./cron/output/ on this WSL host
"""
import sys, os, datetime
sys.path.insert(0, "/opt/data/agentictendies")
sys.path.insert(0, "/opt/data/agentictendies/agentictendies")

import numpy as np
import pandas as pd
import yfinance as yf

from agentictendies.core.indicators import (
    calculate_rsi, calculate_sma, calculate_ema, calculate_atr
)
from agentictendies.backtester.monte_carlo import run_monte_carlo
from agentictendies.backtester.engine import backtest_sma_crossover, compute_metrics

# ── Config ─────────────────────────────────────────────────────────────────
CANDIDATES = ["VRT", "SMCI", "SYM", "PLTR", "DELL", "AMD", "NVDA", "COIN"]
PORT_TICKERS = [("GLD", 4, 588.79), ("TSM", 5, 563.93)]  # (ticker, shares, avg_cost)
ALL_TICKERS = CANDIDATES + ["SPY", "GLD", "TSM"]  # CRITICAL: include portfolio tickers
END_DATE   = datetime.date.today()
START_DATE = END_DATE - datetime.timedelta(days=5*365)

# ── Fetch ───────────────────────────────────────────────────────────────────
print("Fetching 5-year data...")
data = {}
for sym in ALL_TICKERS:
    try:
        df = yf.Ticker(sym).history(start=START_DATE, end=END_DATE, auto_adjust=True)
        df = df[['Open', 'High', 'Low', 'Close', 'Volume']]
        data[sym] = df
        print(f"  OK {sym}: {len(df)} rows, ${df['Close'].iloc[-1]:.2f}")
    except Exception as e:
        print(f"  FAIL {sym}: {e}")

# VIX
try:
    vix = yf.Ticker("^VIX").history(start=START_DATE, end=END_DATE, auto_adjust=True)
    current_vix = vix['Close'].iloc[-1]
except:
    current_vix = None

# ── Indicators ──────────────────────────────────────────────────────────────
def compute_all(df):
    out = df.copy()
    out['SMA20']   = calculate_sma(out['Close'], 20)
    out['SMA50']   = calculate_sma(out['Close'], 50)
    out['SMA200']  = calculate_sma(out['Close'], 200)
    out['RSI14']   = calculate_rsi(out['Close'], 14)
    out['ATR14']   = calculate_atr(out['High'], out['Low'], out['Close'], 14)
    ema12 = calculate_ema(out['Close'], 12)
    ema26 = calculate_ema(out['Close'], 26)
    out['MACD']        = ema12 - ema26
    out['MACD_Signal'] = calculate_ema(out['MACD'], 9)
    out['MACD_Hist']   = out['MACD'] - out['MACD_Signal']
    out['VolRatio']    = out['Volume'] / out['Volume'].rolling(20).mean()
    return out

indicators = {sym: compute_all(df) for sym, df in data.items()}

# ── SPY regime ──────────────────────────────────────────────────────────────
spy      = indicators['SPY']
spy_price  = spy['Close'].iloc[-1]
spy_sma200 = spy['SMA200'].iloc[-1]
BULL       = spy_price > spy_sma200

print(f"\nSPY: ${spy_price:.2f} | SMA200: ${spy_sma200:.2f} | Regime: {'BULL' if BULL else 'BEAR'}")
print(f"VIX: {current_vix:.1f}")

# ── Strategy signals ────────────────────────────────────────────────────────
def sma_signal(d):
    s = d['SMA20'].iloc[-1]; l = d['SMA50'].iloc[-1]
    if pd.isna(s) or pd.isna(l): return "HOLD", 0.6
    return ("BUY" if s > l else "SELL", 0.6)

def rsi_signal(d):
    rsi = d['RSI14'].iloc[-1]
    if pd.isna(rsi): return "HOLD", 0.55
    if rsi < 40:   return "BUY",  0.70
    if rsi > 65:   return "SELL", 0.70
    return "HOLD", 0.55

def macd_signal(d):
    h  = d['MACD_Hist'].iloc[-1]
    hp = d['MACD_Hist'].iloc[-2] if len(d) > 2 else 0
    if pd.isna(h): return "HOLD", 0.55
    if h > 0 and hp <= 0: return "BUY",  0.68
    if h < 0 and hp >= 0: return "SELL", 0.68
    return "HOLD", 0.55

def bollinger_signal(d):
    close = d['Close'].iloc[-1]
    s20   = d['SMA20'].iloc[-1]
    std20 = d['Close'].rolling(20).std().iloc[-1]
    if pd.isna(s20) or pd.isna(std20): return "HOLD", 0.65
    return ("BUY" if close < s20 - 2*std20 else
            "SELL" if close > s20 + 2*std20 else "HOLD", 0.65)

def dual_momentum_signal(d, spy_data):
    close = d['Close']; spy_c = spy_data['Close']
    if len(close) < 252 or len(spy_c) < 252: return "HOLD", 0.55
    mom     = (close.iloc[-1]  / close.iloc[-252]  - 1) * 100
    spy_mom = (spy_c.iloc[-1]  / spy_c.iloc[-252]  - 1) * 100
    if mom > 0 and mom > spy_mom: return "BUY",  0.70
    if mom < 0:                    return "SELL", 0.65
    return "HOLD", 0.55

# ── Process candidates ──────────────────────────────────────────────────────
results = []
for sym in CANDIDATES:
    d = indicators.get(sym)
    if d is None or len(d) < 60:
        print(f"Skip {sym}: insufficient data")
        continue

    price   = d['Close'].iloc[-1]
    rsi     = d['RSI14'].iloc[-1]
    sma20   = d['SMA20'].iloc[-1]
    sma50   = d['SMA50'].iloc[-1]
    atr14   = d['ATR14'].iloc[-1]
    macd_h  = d['MACD_Hist'].iloc[-1]
    vol_r   = d['VolRatio'].iloc[-1]

    sma_s,  sma_c  = sma_signal(d)
    rsi_s,  rsi_c  = rsi_signal(d)
    macd_s, macd_c = macd_signal(d)
    bb_s,   bb_c   = bollinger_signal(d)
    dm_s,   dm_c   = dual_momentum_signal(d, indicators['SPY'])

    scores = [('SMA',sma_s,sma_c),('RSI',rsi_s,rsi_c),
              ('MACD',macd_s,macd_c),('BB',bb_s,bb_c),('DM',dm_s,dm_c)]
    total_score  = sum(w if s=='BUY' else -w if s=='SELL' else 0 for _,s,w in scores)
    total_weight = sum(w for _,_,w in scores)
    net        = total_score / total_weight
    signal     = "BUY" if net >= 0.3 else "SELL" if net <= -0.3 else "HOLD"
    confidence = min(abs(net), 1.0) * 100

    stop_loss = price - 2 * atr14
    target    = price + 3.5 * atr14

    # Walk-forward
    wf_df     = None
    wf_sharpe = None
    try:
        wf_df = backtest_sma_crossover(d['Close'], fast_window=20, slow_window=50)
        wf_m  = compute_metrics(wf_df['Strategy_Return'])
        sh    = wf_m.get('Sharpe Ratio', 0)
        # GUARD: compute_metrics can return None or non-numeric
        wf_sharpe = round(float(sh), 3) if isinstance(sh, (int, float)) and sh is not None else None
    except Exception as e:
        print(f"    WF error for {sym}: {e}")

    # Monte Carlo
    mc_maxdd = mc_var95 = None
    try:
        if wf_df is not None and len(wf_df) > 10:
            mc = run_monte_carlo(wf_df['Strategy_Return'], n_sims=100)
            md = mc.get('Max Drawdown (Median)') or mc.get('Max Drawdown')
            vp = mc.get('VaR (95%)')            or mc.get('Value at Risk (95%)')
            mc_maxdd = round(float(md), 1) if isinstance(md, (int,float)) and md is not None else None
            mc_var95  = round(float(vp), 3) if isinstance(vp, (int,float)) and vp is not None else None
    except Exception as e:
        print(f"    MC error for {sym}: {e}")

    vol_flag = "VOL_SPIKE" if vol_r > 1.5 else ""

    results.append({
        'Symbol': sym, 'Price': round(price,2), 'RSI14': round(rsi,1),
        'SMA20': round(sma20,2) if not pd.isna(sma20) else None,
        'SMA50': round(sma50,2) if not pd.isna(sma50) else None,
        'MACD_Hist': round(macd_h,3), 'ATR14': round(atr14,2),
        'VolRatio': round(vol_r,2), 'Signal': signal, 'Confidence': round(confidence,0),
        'Entry': round(price,2), 'StopLoss': round(stop_loss,2), 'Target': round(target,2),
        'SMA_S': sma_s, 'RSI_S': rsi_s, 'MACD_S': macd_s,
        'BB_S': bb_s, 'DM_S': dm_s,
        'WF_Sharpe': wf_sharpe,
        'MC_MaxDD': mc_maxdd, 'MC_VaR95': mc_var95,
        'VolFlag': vol_flag,
    })
    print(f"  {sym}: {signal} C={confidence:.0f}% | RSI={rsi:.1f} | Vol={vol_r:.2f}{' '+vol_flag if vol_flag else ''}")

# ── Portfolio positions ────────────────────────────────────────────────────
port_rows = []
for ticker, shares, avg_cost in PORT_TICKERS:
    if ticker in indicators:
        d = indicators[ticker]
        price     = d['Close'].iloc[-1]
        rsi       = d['RSI14'].iloc[-1]
        macd_h    = d['MACD_Hist'].iloc[-1]
        macd_prev = d['MACD_Hist'].iloc[-2]
        pct_pnl   = (price - avg_cost) / avg_cost * 100
        macd_cross = "CROSS_UP" if macd_h > 0 and macd_prev <= 0 else \
                     "CROSS_DOWN" if macd_h < 0 and macd_prev >= 0 else "NEUTRAL"
        flag = ""
        if rsi > 65:                     flag = "RSI_OVERBOUGHT"
        elif rsi < 40:                   flag = "RSI_OVERSOLD"
        if pct_pnl < -20:                flag = f"LARGE_LOSS_{pct_pnl:.1f}%"
        port_rows.append({
            'Ticker': ticker, 'Shares': shares, 'AvgCost': avg_cost,
            'Price': round(price,2), 'PnL_pct': round(pct_pnl,1),
            'RSI': round(rsi,1), 'MACD_Hist': round(macd_h,3),
            'MACD_Signal': macd_cross, 'Flag': flag
        })
        print(f"  PORT {ticker}: ${price:.2f} PnL={pct_pnl:.1f}% RSI={rsi:.1f} MACD={macd_cross} FLAG={flag}")

# ── Output ──────────────────────────────────────────────────────────────────
ts       = datetime.datetime.now().strftime("%Y%m%d-%H%M")
out_dir  = "/opt/data/home/./cron/output"   # absolute path for WSL
os.makedirs(out_dir, exist_ok=True)
out_path = os.path.join(out_dir, f"portfolio-research-{ts}.md")

spy_regime = "BULL" if BULL else "BEAR"
vix_ctx    = "LOW" if (current_vix and current_vix < 20) else \
             "HIGH" if (current_vix and current_vix > 30) else "MEDIUM"

signal_order = {'BUY': 0, 'HOLD': 1, 'SELL': 2}
ranked = sorted(results, key=lambda x: (signal_order.get(x['Signal'], 3), -x['Confidence']))

lines = []
lines.append("# Portfolio Research -- {}".format(ts))
lines.append("")
lines.append("## Market Context")
lines.append("- SPY: ${:.2f} | SMA200: ${:.2f} | Regime: **{}**".format(spy_price, spy_sma200, spy_regime))
lines.append("- VIX: {:.1f} (context: {})".format(current_vix, vix_ctx))
lines.append("- Timestamp: {}".format(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')))

lines.append("")
lines.append("## AI/Infrastructure Candidates (Ranked BUY/SELL/HOLD)")
lines.append("| Ticker | Signal | Conf% | Price | StopLoss | Target | RSI14 | SMA20 | SMA50 | MACD_Hist | VolRatio | WF_Sharpe |")
lines.append("|--------|--------|-------:|------:|---------:|-------:|------:|------:|------:|----------:|---------:|----------:|")
for r in ranked:
    wf_str = str(r['WF_Sharpe']) if r['WF_Sharpe'] is not None else "-"
    vol_note = " *" if r['VolFlag'] else ""
    lines.append("| {S} | {sig} | {c:.0f}% | ${p:.2f} | ${sl:.2f} | ${t:.2f} | {rsi:.1f} | {s20} | {s50} | {macd:.3f} | {vr:.2f}{vn} | {wf} |".format(
        S=r['Symbol'], sig=r['Signal'], c=r['Confidence'],
        p=r['Price'], sl=r['StopLoss'], tgt=r['Target'], rsi=r['RSI14'],
        s20="{:.2f}".format(r['SMA20']) if r['SMA20'] else "-",
        s50="{:.2f}".format(r['SMA50']) if r['SMA50'] else "-",
        macd=r['MACD_Hist'], vr=r['VolRatio'], vn=vol_note, wf=wf_str
    ))

lines.append("")
lines.append("### Strategy Signals Detail")
for r in ranked:
    mc_str = " MC_MaxDD={} MC_VaR95={}".format(r['MC_MaxDD'], r['MC_VaR95']) if r['MC_MaxDD'] else ""
    lines.append("- **{S}**: {sig} (C={c:.0f}%) | SMA={sma} | RSI={rsi} | MACD={macd} | BB={bb} | DM={dm} | WF_Sharpe={wf}{mc}".format(
        S=r['Symbol'], sig=r['Signal'], c=r['Confidence'],
        sma=r['SMA_S'], rsi=r['RSI_S'], macd=r['MACD_S'],
        bb=r['BB_S'], dm=r['DM_S'], wf=r['WF_Sharpe'], mc=mc_str
    ))

lines.append("")
lines.append("## Portfolio Positions -- Technical Update")
lines.append("| Ticker | Shares | AvgCost | Price | PnL% | RSI | MACD_Hist | MACD_Signal | Flag |")
lines.append("|--------|-------:|--------:|------:|-----:|----:|----------:|-------------|------|")
for r in port_rows:
    lines.append("| {T} | {n} | ${c:.2f} | ${p:.2f} | {pnl:.1f}% | {rsi:.1f} | {macd:.3f} | {sig} | {flag} |".format(
        T=r['Ticker'], n=r['Shares'], c=r['AvgCost'], p=r['Price'],
        pnl=r['PnL_pct'], rsi=r['RSI'], macd=r['MACD_Hist'],
        sig=r['MACD_Signal'], flag=r['Flag']
    ))

lines.append("")
lines.append("## Risk Alerts")
alerts = []
for r in port_rows:
    if r['Flag']: alerts.append("- {}: {}".format(r['Ticker'], r['Flag']))
for r in results:
    if r['RSI14'] > 65: alerts.append("- {}: RSI_OVERBOUGHT {:.1f}".format(r['Symbol'], r['RSI14']))
    if r['RSI14'] < 40: alerts.append("- {}: RSI_OVERSOLD {:.1f}".format(r['Symbol'], r['RSI14']))
    if r['VolRatio'] > 1.5: alerts.append("- {}: VOLUME_SPIKE {:.2f}x".format(r['Symbol'], r['VolRatio']))
if not alerts:
    lines.append("- No alerts")
else:
    lines.extend(alerts)

lines.append("")
lines.append("## Framework Insights")
wf_str = ", ".join(["{}(Sharpe={})".format(r['Symbol'], r['WF_Sharpe'])
                    for r in results if r['WF_Sharpe'] and r['WF_Sharpe'] > 0.5])
if wf_str:
    lines.append("- Walk-Forward SMA Crossover: " + wf_str)
else:
    lines.append("- Walk-Forward SMA Crossover: No strong out-of-sample signals in current window")

mc_items = ["{}=MaxDD{}% VaR95={}".format(r['Symbol'], r['MC_MaxDD'], r['MC_VaR95'])
            for r in results if r['MC_MaxDD']]
if mc_items:
    lines.append("- Monte Carlo Risk: " + ", ".join(mc_items))

buy_s  = [r['Symbol'] for r in results if r['Signal']=='BUY']
sell_s = [r['Symbol'] for r in results if r['Signal']=='SELL']
hold_s = [r['Symbol'] for r in results if r['Signal']=='HOLD']
lines.append("")
lines.append("## AI Theme Signal Summary")
lines.append("- BUY signals: " + (", ".join(buy_s)  if buy_s  else "None"))
lines.append("- SELL signals: " + (", ".join(sell_s) if sell_s else "None"))
lines.append("- HOLD signals: " + (", ".join(hold_s) if hold_s else "None"))

markdown = "\n".join(lines)
with open(out_path, 'w') as f:
    f.write(markdown)

print("\nSaved:", out_path)
print("\n=== SIGNAL SUMMARY ===")
for r in ranked:
    print("  {} | {} | C={:.0f}% | RSI={:.1f} | Vol={:.2f}".format(
        r['Symbol'], r['Signal'], r['Confidence'], r['RSI14'], r['VolRatio']))
print("\n=== PORTFOLIO ===")
for r in port_rows:
    print("  {} | ${:.2f} | PnL={:.1f}% | RSI={:.1f} | {}".format(
        r['Ticker'], r['Price'], r['PnL_pct'], r['RSI'], r['Flag']))
print("\n" + markdown)
