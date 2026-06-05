# VRT Technical Analysis — Interactive Session Script
# Date: 2026-05-28
# Task: Live technical snapshot + 3-strategy backtest simulation for VRT at $320.19
# Stack: QuantDinger REST API + AgenticTendies core.indicators (pandas-based)
#
# Key finding: Stochastic %K=17.7 (极度超卖) vs RSI=46.8 (中性) = 底背离信号
# MACD histogram 仍为负，短期有回调压力，但 EMA12>EMA26 金叉确认中期趋势向上
# 建议：可少量建仓，等 RSI<40 或回落到 $306(SMA50) 再加仓

import urllib.request, json, sys, math
from datetime import datetime
sys.path.insert(0, "/opt/data/agentictendies")
import pandas as pd
from agentictendies.core.indicators import (
    calculate_rsi, calculate_sma, calculate_ema, calculate_atr
)

TOKEN = "qd_agent_TWSkB8spR49Kuccw_WMEaVl0L18YyVQG6PaVt6OJ7nM"
BASE  = "http://localhost:8888"

def get_json(path, params=None):
    url = f"{BASE}{path}"
    if params:
        url += "?" + "&".join(f"{k}={v}" for k, v in params.items())
    req = urllib.request.Request(url)
    req.add_header("Authorization", f"Bearer {TOKEN}")
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read())

# ─── Fetch 90 days of daily bars ──────────────────────────────────
klines = get_json("/api/agent/v1/klines", {
    "market": "USStock", "symbol": "VRT", "timeframe": "1d", "limit": 90
})
bars = klines["data"]["klines"]

df = pd.DataFrame(bars)
df["time"] = pd.to_datetime(df["time"], unit="s")
df = df.sort_values("time").reset_index(drop=True)
df.rename(columns={
    "time": "date", "close": "Close", "high": "High",
    "low": "Low", "volume": "Volume"
}, inplace=True)

closes = df["Close"].tolist()
highs  = df["High"].tolist()
lows   = df["Low"].tolist()
vols   = df["Volume"].tolist()
dates  = df["date"].tolist()
n      = len(df)
lv     = n - 1

# ─── Indicators (all return pd.Series aligned with input) ─────────
rsi14  = calculate_rsi(df["Close"], 14)
sma20  = calculate_sma(df["Close"], 20)
sma50  = calculate_sma(df["Close"], 50)
ema12  = calculate_ema(df["Close"], 12)
ema26  = calculate_ema(df["Close"], 26)
atr14  = calculate_atr(df["High"], df["Low"], df["Close"], 14)

# MACD — computed inline (not in indicators.py)
ema_f  = calculate_ema(df["Close"], 12)
ema_s  = calculate_ema(df["Close"], 26)
macd_l = ema_f - ema_s
macd_s = calculate_ema(macd_l, 9)
macd_h = macd_l - macd_s  # histogram

# Bollinger Bands — inline
std20  = df["Close"].rolling(20).std()
bb_mid = calculate_sma(df["Close"], 20)
bb_up  = bb_mid + 2 * std20
bb_lo  = bb_mid - 2 * std20

# Stochastic %K — inline
roll_low  = df["Low"].rolling(14).min()
roll_high = df["High"].rolling(14).max()
stoch_k   = 100 * (df["Close"] - roll_low) / (roll_high - roll_low + 1e-9)
stoch_d   = stoch_k.rolling(3).mean()

# ─── Current values ───────────────────────────────────────────────
price  = float(df["Close"].iloc[lv])
rsi_v  = float(rsi14.iloc[lv])   if not pd.isna(rsi14.iloc[lv])   else None
sma20v = float(sma20.iloc[lv])  if not pd.isna(sma20.iloc[lv])  else None
sma50v = float(sma50.iloc[lv])  if not pd.isna(sma50.iloc[lv])  else None
ema12v = float(ema12.iloc[lv])  if not pd.isna(ema12.iloc[lv])  else None
ema26v = float(ema26.iloc[lv])  if not pd.isna(ema26.iloc[lv])  else None
atr_v  = float(atr14.iloc[lv])   if not pd.isna(atr14.iloc[lv])   else None
mlv    = float(macd_l.iloc[lv]) if not pd.isna(macd_l.iloc[lv]) else None
slv    = float(macd_s.iloc[lv]) if not pd.isna(macd_s.iloc[lv]) else None
mhv    = float(macd_h.iloc[lv]) if not pd.isna(macd_h.iloc[lv]) else None
buv    = float(bb_up.iloc[lv])  if not pd.isna(bb_up.iloc[lv])  else None
bmv    = float(bb_mid.iloc[lv]) if not pd.isna(bb_mid.iloc[lv]) else None
blv    = float(bb_lo.iloc[lv])  if not pd.isna(bb_lo.iloc[lv])  else None
skv    = float(stoch_k.iloc[lv]) if not pd.isna(stoch_k.iloc[lv]) else None
sdv    = float(stoch_d.iloc[lv]) if not pd.isna(stoch_d.iloc[lv]) else None

# ─── Print Technical Snapshot ─────────────────────────────────────
def fm(v):      return f"${v:.2f}" if v is not None else "N/A"
def fp(v, d=1): return f"{v:.{d}f}" if v is not None else "N/A"

now = dates[lv].strftime("%Y-%m-%d")
sep = "=" * 62
print(f"\n{sep}")
print(f"  VRT  TECHNICAL SNAPSHOT  ({now})")
print(sep)
print(f"  Price:          {fm(price)}")
print(f"  RSI(14):        {fp(rsi_v)}   {'🟢 OVERSOLD' if rsi_v and rsi_v<40 else '🔴 OVERBOUGHT' if rsi_v and rsi_v>70 else '⚪ NEUTRAL'}")
print(f"  Stochastic %K: {fp(skv)}   %D: {fp(sdv)}")
print(f"  SMA(20):        {fm(sma20v)}   {'▲' if price>sma20v else '▼'} price")
print(f"  SMA(50):        {fm(sma50v)}   {'▲' if price>sma50v else '▼'} price")
print(f"  EMA(12/26):    {fm(ema12v)} / {fm(ema26v)}   {'▲ 金叉' if ema12v and ema26v and ema12v>ema26v else '▼ 死叉'}")
print(f"  MACD:          {fp(mlv,3)}  signal: {fp(slv,3)}  hist: {fp(mhv,3)}")
print(f"  Bollinger:     {fm(buv)} / {fm(bmv)} / {fm(blv)}")
print(f"  ATR(14):        {fm(atr_v)}")
avg_v20 = sum(vols[-20:]) / 20
print(f"  Vol:           {vols[lv]:,.0f}   ({fp(vols[lv]/avg_v20,2)}x 20d avg)")

# ─── Signal Board ──────────────────────────────────────────────────
sig_list = []
def add(label, sig, score):
    print(f"  {sig}  {label}")
    sig_list.append(score)

print(f"\n  ── SIGNAL BOARD ──")
if rsi_v and rsi_v < 30:    add("RSI < 30 超卖",          "🟢 强烈买入", 3)
elif rsi_v and rsi_v < 40:  add("RSI < 40 偏低",          "🟢 买入机会", 2)
elif rsi_v and rsi_v > 70:  add("RSI > 70 超买",          "🔴 卖出信号", -3)
if price > sma20v:  add("价格 > SMA(20)",  "🟢 中期看多", 1)
if price > sma50v:  add("价格 > SMA(50)",  "🟢 长期看多", 2)
if ema12v and ema26v and ema12v > ema26v: add("EMA12 > EMA26 金叉", "🟢 动量向上", 2)
if ema12v and ema26v and ema12v < ema26v: add("EMA12 < EMA26 死叉", "🔴 动量向下", -2)
if mhv and mhv > 0:  add("MACD histogram+", "🟢 看多", 1)
if mhv and mhv < 0:  add("MACD histogram-", "🔴 看空", -1)
if skv and skv < 20: add("Stoch < 20 超卖",   "🟢 超卖反弹", 2)
if skv and skv > 80: add("Stoch > 80 超买",   "🔴 超买警惕", -2)
if price < blv:     add("触及布林下轨",        "🟢 反弹机会", 2)
if price > buv:     add("突破布林上轨",        "🔴 警惕",     -1)

score = sum(sig_list)
verdict = ("🟢 强烈看多" if score >= 5 else "🟢 看多" if score > 0
           else "🔴 看空" if score < 0 else "⚪ 中性")
print(f"\n  Composite Score: {score:+d}  →  {verdict}")
print(sep)

# ─── 3-Strategy Backtest ─────────────────────────────────────────
strategies = {
    "RSI Reversion (RSI<40→RSI>50)": {"entry_rsi": 40, "exit_rsi": 50, "min_bars": 5},
    "Golden Cross + RSI Confirm":    {"ema_cross_long": True, "entry_rsi_max": 65, "rsi_min": 40},
    "Buy-the-Dip (RSI<35)":          {"entry_rsi": 35, "atr_sl": 2.0, "atr_tp": 3.5}
}

for strat_name, params in strategies.items():
    capital = 10_000.0
    position = 0; shares = 0; entry = 0.0
    trades = []; wins = 0; losses = 0
    win_amt = []; loss_amt = []

    for i in range(50, n):  # start where all indicators valid
        c      = closes[i]
        rsi_i  = float(rsi14.iloc[i]) if not pd.isna(rsi14.iloc[i]) else 50
        atr_i  = float(atr14.iloc[i]) if not pd.isna(atr14.iloc[i]) else 1.0
        ema12_i = float(ema12.iloc[i]) if not pd.isna(ema12.iloc[i]) else c
        ema26_i = float(ema26.iloc[i]) if not pd.isna(ema26.iloc[i]) else c
        sma20_i = float(sma20.iloc[i]) if not pd.isna(sma20.iloc[i]) else c
        sma50_i = float(sma50.iloc[i]) if not pd.isna(sma50.iloc[i]) else c
        date_i  = dates[i].strftime("%Y-%m-%d")

        if strat_name == "RSI Reversion (RSI<40→RSI>50)":
            if position == 0 and rsi_i < params["entry_rsi"]:
                shares = int(capital / c); entry = c; position = 1
                trades.append({"date": date_i, "type": "BUY", "price": c, "shares": shares, "rsi": rsi_i})
                capital -= shares * c; bars_held = 0
            elif position == 1:
                bars_held += 1
                if rsi_i > params["exit_rsi"] and bars_held >= params["min_bars"]:
                    pnl = (c - entry) * shares
                    if pnl > 0: wins += 1; win_amt.append(pnl)
                    else: losses += 1; loss_amt.append(abs(pnl))
                    trades.append({"date": date_i, "type": "SELL", "price": c, "rsi": rsi_i, "pnl": pnl})
                    capital += shares * c; position = 0; shares = 0

        elif strat_name == "Golden Cross + RSI Confirm":
            if position == 0 and ema12_i > ema26_i and sma20_i > sma50_i and params["rsi_min"] <= rsi_i <= params["entry_rsi_max"]:
                shares = int(capital / c); entry = c; position = 1
                trades.append({"date": date_i, "type": "BUY", "price": c, "shares": shares, "rsi": rsi_i})
                capital -= shares * c; bars_held = 0
            elif position == 1:
                bars_held += 1
                if ema12_i < ema26_i or rsi_i > 70 or bars_held >= 30:
                    pnl = (c - entry) * shares
                    if pnl > 0: wins += 1; win_amt.append(pnl)
                    else: losses += 1; loss_amt.append(abs(pnl))
                    trades.append({"date": date_i, "type": "SELL", "price": c, "rsi": rsi_i, "pnl": pnl})
                    capital += shares * c; position = 0; shares = 0

        elif strat_name == "Buy-the-Dip (RSI<35)":
            if position == 0 and rsi_i < params["entry_rsi"]:
                shares = int(capital / c); entry = c; position = 1
                sl = c - params["atr_sl"] * atr_i
                tp = c + params["atr_tp"] * atr_i
                trades.append({"date": date_i, "type": "BUY", "price": c, "shares": shares, "rsi": rsi_i})
                capital -= shares * c
            elif position == 1:
                if c <= sl or c >= tp:
                    pnl = (c - entry) * shares
                    if pnl > 0: wins += 1; win_amt.append(pnl)
                    else: losses += 1; loss_amt.append(abs(pnl))
                    reason = "SL" if c <= sl else "TP"
                    trades.append({"date": date_i, "type": "SELL", "price": c, "rsi": rsi_i, "pnl": pnl, "reason": reason})
                    capital += shares * c; position = 0; shares = 0

    if position == 1:
        capital += shares * closes[-1]
        trades.append({"date": dates[-1].strftime("%Y-%m-%d"), "type": "CLOSE", "price": closes[-1]})

    total_ret = (capital - 10_000) / 10_000 * 100
    wr = wins / (wins + losses) * 100 if (wins + losses) > 0 else 0
    pf = sum(win_amt) / sum(loss_amt) if loss_amt else float("inf")
    bh_ret = (closes[-1] - closes[50]) / closes[50] * 100

    print(f"\n  ── {strat_name} ──")
    print(f"    Final: ${capital:.2f} ({total_ret:+.1f}%)  Trades:{wins+losses}(W:{wins} L:{losses})  WR:{wr:.0f}%  PF:{pf:.2f}x  B&H:{bh_ret:+.1f}%")
    for t in trades:
        e = "🟢" if t["type"] == "BUY" else "🔴"
        rs = f"RSI:{t['rsi']:.0f}" if "rsi" in t else ""
        pn = f" PnL:{t['pnl']:+.0f}" if "pnl" in t else ""
        rx = f"[{t.get('reason','')}]" if t["type"] == "SELL" and "reason" in t else ""
        print(f"      {e} {t['date']} {t['type']:5s} @${t['price']:.2f} {rs}{pn}{rx}")

print()
print(sep)
print("  FINAL VERDICT")
print(sep)
print(f"  Current: {fm(price)}  RSI:{rsi_v:.1f}  Stoch%K:{skv:.1f}")
print(f"  ATR(14): {fm(atr_v)}")
print(f"  Stop Loss:   {fm(price - 2*atr_v)} (-{100*2*atr_v/price:.1f}%)")
print(f"  Take Profit: {fm(price + 3.5*atr_v)} (+{100*3.5*atr_v/price:.1f}%)")
print(f"  Risk/Reward: 1 : {(3.5*atr_v)/(2*atr_v):.1f}")
print(f"  → {'建议当前价位少量建仓' if rsi_v and rsi_v < 50 else '等RSI<40或回落到SMA50支撑再买'}")
print(sep)