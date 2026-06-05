"""
Portfolio Research Cron Template — QuantDinger + AgenticTendies
==============================================================
Based on the verified Jun 2 2026 11:34 run.

Pipeline:
1. Fetch klines for 7 AI/infra tickers from QuantDinger (limit=250)
2. Compute RSI(14), SMA(20/50), MACD(hist+state), Stochastic K/D,
   ATR(14), Bollinger Bands, volume ratio
3. Apply signal logic (RSI<40 BUY, >70 SELL, 40-55+SMA20 BUY, else HOLD)
4. Rank by confidence = |RSI-50| + |trend%| * 0.5
5. Fetch live prices for portfolio tickers (GLD, TSM)
6. Write markdown to 3 cron output paths
7. Compose short Chinese Discord message

Run:
    /opt/data/agentictendies/.venv/bin/python portfolio_research_template.py
"""
import os, sys, json, urllib.request
from datetime import datetime

import pandas as pd
sys.path.insert(0, "/opt/data/agentictendies")
from agentictendies.core.indicators import (
    calculate_rsi, calculate_sma, calculate_ema, calculate_atr
)

# --- CONFIG ---
TOKEN = os.environ.get(
    "QUANTDINGER_TOKEN",
    "qd_agent_TWSkB8spR49Kuccw_WMEaVl0L18YyVQG6PaVt6OJ7nM",
)
BASE = os.environ.get("QUANTDINGER_BASE", "http://localhost:8888")
CANDIDATES = ["VRT", "SMCI", "PLTR", "AMD", "NVDA", "COIN", "DELL"]
PORTFOLIO = [("GLD", 4, 588.79), ("TSM", 5, 563.93)]
JOB_ID = "f2f177230acb"


# --- INLINE INDICATORS (not in agentictendies.core.indicators) ---
def stoch_kd(klines, period=14, k_smooth=3, d_smooth=3):
    """Stochastic %K and %D. Returns (k, d) or (None, None)."""
    if len(klines) < period + k_smooth + d_smooth:
        return None, None
    closes = pd.Series([k["close"] for k in klines])
    lows = pd.Series([k["low"] for k in klines])
    highs = pd.Series([k["high"] for k in klines])
    hh = highs.rolling(period).max()
    ll = lows.rolling(period).min()
    raw_k = (100 * (closes - ll) / (hh - ll).replace(0, pd.NA)).fillna(50.0)
    k = raw_k.rolling(k_smooth).mean()
    d = k.rolling(d_smooth).mean()
    return float(k.iloc[-1]), float(d.iloc[-1])


def bollinger(closes, period=20, num_std=2.0):
    """Returns (upper, mid, lower) Bollinger Bands."""
    if len(closes) < period:
        return None, None, None
    s = pd.Series(closes, dtype=float)
    mid = s.rolling(period).mean()
    sd = s.rolling(period).std()
    return (
        float((mid + num_std * sd).iloc[-1]),
        float(mid.iloc[-1]),
        float((mid - num_std * sd).iloc[-1]),
    )


def macd_state(closes):
    """Returns (macd, signal, hist, state)."""
    if len(closes) < 35:
        return None, None, None, None
    s = pd.Series(closes, dtype=float)
    ema12 = calculate_ema(s, 12)
    ema26 = calculate_ema(s, 26)
    macd = ema12 - ema26
    sig = calculate_ema(macd, 9)
    hist = macd - sig
    return (
        float(macd.iloc[-1]),
        float(sig.iloc[-1]),
        float(hist.iloc[-1]),
        "BULL" if macd.iloc[-1] > sig.iloc[-1] else "BEAR",
    )


def vol_ratio(klines, lookback=20):
    """Today's volume / 20d avg (excluding today)."""
    if len(klines) < lookback:
        return None
    vols = [float(k.get("volume", 0)) for k in klines[-lookback:]]
    avg = sum(vols[:-1]) / (lookback - 1) if vols[:-1] else 0
    return vols[-1] / avg if avg > 0 else 1.0


# --- QUANTDINGER ---
def _get(path):
    req = urllib.request.Request(f"{BASE}{path}")
    req.add_header("Authorization", f"Bearer {TOKEN}")
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read())


def fetch_klines(sym, limit=250):
    try:
        d = _get(
            f"/api/agent/v1/klines?market=USStock&symbol={sym}"
            f"&timeframe=1d&limit={limit}"
        )
        return d.get("data", {}).get("klines", [])
    except Exception as e:
        print(f"[klines err] {sym}: {e}", file=sys.stderr)
        return []


def fetch_price(sym):
    try:
        d = _get(f"/api/agent/v1/price?market=USStock&symbol={sym}")
        p = d.get("data", {}).get("price")
        if p is not None:
            return float(p)
    except Exception:
        pass
    k = fetch_klines(sym, 5)
    return float(k[-1]["close"]) if k else None


# --- ANALYZE ---
def analyze(sym):
    klines = fetch_klines(sym, 250)
    if not klines or len(klines) < 30:
        return {"ticker": sym, "error": "no data", "bar_count": len(klines)}
    closes = [float(k["close"]) for k in klines]
    highs = [float(k["high"]) for k in klines]
    lows = [float(k["low"]) for k in klines]
    last_close = closes[-1]
    cs = pd.Series(closes, dtype=float)
    hs = pd.Series(highs, dtype=float)
    ls = pd.Series(lows, dtype=float)
    rsi = float(calculate_rsi(cs, 14).iloc[-1])
    sma20 = float(calculate_sma(cs, 20).iloc[-1])
    sma50 = float(calculate_sma(cs, 50).iloc[-1]) if len(closes) >= 50 else None
    atr14 = float(calculate_atr(hs, ls, cs, 14).iloc[-1])
    sk, sd = stoch_kd(klines, 14)
    vr = vol_ratio(klines, 20)
    m, ms, mh, mstate = macd_state(closes)
    up, mid, lo = bollinger(closes, 20, 2.0)

    # Signal logic (priority order)
    if rsi < 40: signal = "BUY"
    elif rsi > 70: signal = "SELL"
    elif 40 <= rsi < 55 and last_close > sma20: signal = "BUY"
    elif 40 <= rsi < 55: signal = "HOLD"
    elif 55 <= rsi <= 70: signal = "SELL"
    else: signal = "HOLD"

    golden_cross = sma50 is not None and sma20 > sma50
    rsi_dist = abs(rsi - 50)
    trend_pct = (last_close - sma20) / sma20 * 100
    confidence = round(rsi_dist + abs(trend_pct) * 0.5, 2)

    if up is None or lo is None or up == lo: bb_pos = "N/A"
    elif last_close > up: bb_pos = "上轨"
    elif last_close < lo: bb_pos = "下轨"
    else: bb_pos = "中轨"

    return {
        "ticker": sym, "bar_count": len(klines),
        "price": round(last_close, 2), "rsi14": round(rsi, 1),
        "sma20": round(sma20, 2), "sma50": round(sma50, 2) if sma50 else None,
        "atr14": round(atr14, 2),
        "stoch_k": round(sk, 1) if sk is not None else None,
        "stoch_d": round(sd, 1) if sd is not None else None,
        "vol_ratio": round(vr, 2) if vr else None,
        "macd_hist": round(mh, 2) if mh is not None else None,
        "macd_state": mstate, "bb_pos": bb_pos,
        "golden_cross": golden_cross, "trend_pct": round(trend_pct, 2),
        "signal": signal, "confidence": confidence,
    }


# --- MAIN ---
def main():
    results = {}
    for sym in CANDIDATES:
        try:
            r = analyze(sym)
            if r: results[sym] = r
        except Exception as e:
            results[sym] = {"ticker": sym, "error": str(e)}

    ranked = sorted(
        [r for r in results.values() if "error" not in r],
        key=lambda x: x["confidence"], reverse=True,
    )

    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    tsf = datetime.now().strftime("%Y%m%d-%H%M")

    md = [f"# 📊 AI/基础设施技术分析报告",
          f"**生成时间**: {ts} (每15分钟自动更新)", ""]
    md.append("## 🏆 信号排行榜（置信度排序）"); md.append("")
    md.append("| 排名 | 股票 | 现价 | 信号 | RSI(14) | SMA20 | MACD柱 | "
              "随机K/D | 成交量比 | 布林带 | 置信度 |")
    md.append("|---:|---:|---:|:---:|---:|---:|---:|---:|---:|:---:|---:|")
    for i, r in enumerate(ranked, 1):
        sig = {"BUY": "🟢 BUY", "SELL": "🔴 SELL", "HOLD": "🟡 HOLD"}.get(
            r["signal"], r["signal"])
        skd = (f"{r['stoch_k']}/{r['stoch_d']}"
               if r["stoch_k"] is not None else "N/A")
        md.append(
            f"| {i} | **{r['ticker']}** | ${r['price']} | {sig} | {r['rsi14']} | "
            f"${r['sma20']} | {r['macd_hist']} | {skd} | x{r['vol_ratio']} | "
            f"{r['bb_pos']} | **{r['confidence']}** |"
        )
    md.append("")
    md.append("### 📌 信号规则")
    md.append("- 🟢 **BUY**: RSI < 40（超卖）或 RSI 40-55 + 价格站稳SMA20")
    md.append("- 🔴 **SELL**: RSI > 70（超买）")
    md.append("- 🟡 **HOLD**: 趋势不明，观望")
    md.append("")

    valid = [r for r in ranked if r.get("rsi14") is not None]
    avg_rsi = sum(r["rsi14"] for r in valid) / len(valid) if valid else 0
    ob = sum(1 for r in valid if r["rsi14"] > 70)
    os_ = sum(1 for r in valid if r["rsi14"] < 40)
    md.append("## 📈 市场情绪总览")
    md.append("| 指标 | 数值 |"); md.append("|---|---:|")
    md.append(f"| 板块平均RSI | **{avg_rsi:.1f}** |")
    md.append(f"| 超买个股 (RSI>70) | {ob} |")
    md.append(f"| 超卖个股 (RSI<40) | {os_} |")
    sentiment = ("⚠️ 板块超卖，关注反转" if os_ else
                 ("⚠️ 板块超买，谨慎追高" if ob >= 3 else
                  ("📈 板块偏多" if avg_rsi > 55 else "✅ 中性")))
    md.append(f"| 情绪 | {sentiment} |")
    md.append("")

    md.append("## 💼 持仓状况 (TD Direct — 41HHH9A)")
    md.append(""); md.append("| 股票 | 股数 | 均价 | 现价 | 盈亏($) | 盈亏(%) |")
    md.append("|---|---:|---:|---:|---:|---:|")
    total_mv = total_cost = 0
    for sym, sh, cost in PORTFOLIO:
        px = fetch_price(sym) or cost
        mv = sh * px; pnl = (px - cost) * sh; pct = (px - cost) / cost * 100
        total_mv += mv; total_cost += sh * cost
        e = "🟢" if pnl >= 0 else "🔴"
        md.append(f"| {sym} | {sh} | ${cost:.2f} | ${px:.2f} | "
                  f"{e} ${pnl:+.2f} | {e} {pct:+.2f}% |")
    total_pnl = total_mv - total_cost
    total_pct = total_pnl / total_cost * 100
    e = "🟢" if total_pnl >= 0 else "🔴"
    md.append(f"| **合计** | | **${total_cost:,.2f}** | **${total_mv:,.2f}** | "
              f"{e} **{total_pnl:+.2f}** | {e} **{total_pct:+.2f}%** |")
    md.append("")

    md.append("## 🔍 个股技术解读（置信度前4）")
    for i, r in enumerate(ranked[:4], 1):
        sig = {"BUY": "🟢 BUY", "SELL": "🔴 SELL", "HOLD": "🟡 HOLD"}.get(
            r["signal"], r["signal"])
        md.append(f"### {i}. **{r['ticker']}** @ ${r['price']}")
        md.append("| 指标 | 数值 | 解读 |"); md.append("|---|---|---|")
        rsi_int = ("⚠️ 超买" if r["rsi14"] > 70 else
                   ("⚠️ 超卖" if r["rsi14"] < 30 else
                    ("📉 偏弱" if r["rsi14"] < 40 else "➡️ 中性")))
        md.append(f"| RSI(14) | {r['rsi14']} | {rsi_int} |")
        trend_int = ("✅ 站上SMA20" if r["trend_pct"] > 0
                     else "⚠️ 跌破SMA20")
        md.append(f"| 趋势 | SMA20=${r['sma20']} | "
                  f"{trend_int} ({r['trend_pct']:+.1f}%) |")
        if r["sma50"] is not None:
            gc = "✅ 金叉" if r["golden_cross"] else "❌ 死叉"
            md.append(f"| SMA50 | ${r['sma50']} | {gc} |")
        if r["macd_hist"] is not None:
            macd_int = "📈 看多" if r["macd_state"] == "BULL" else "📉 看空"
            md.append(f"| MACD柱状图 | {r['macd_hist']} | {macd_int} |")
        if r["stoch_k"] is not None:
            s_int = ("高位" if r["stoch_k"] > 80 else
                     ("低位" if r["stoch_k"] < 20 else "中性"))
            md.append(f"| 随机指标 | K={r['stoch_k']} D={r['stoch_d']} | {s_int} |")
        if r["vol_ratio"] is not None:
            vr_int = ("⚠️ 放量异常" if r["vol_ratio"] > 1.5 else
                      ("📉 缩量" if r["vol_ratio"] < 0.5 else "➡️ 正常"))
            md.append(f"| 成交量 | x{r['vol_ratio']} | {vr_int} |")
        md.append(f"| ATR(14) | ${r['atr14']} | 波动率参考 |")
        md.append(f"| **信号** | **{sig}** | 置信度 **{r['confidence']}** |")
        md.append("")

    buys = [r for r in ranked if r["signal"] == "BUY"]
    sells = [r for r in ranked if r["signal"] == "SELL"]
    if buys or sells:
        md.append("## 💡 操作建议"); md.append("")
        for r in buys:
            md.append(f"- 🟢 **BUY {r['ticker']}** @ ${r['price']} — "
                      f"RSI {r['rsi14']}, 趋势 {r['trend_pct']:+.1f}%, "
                      f"置信度 {r['confidence']}")
        for r in sells:
            md.append(f"- 🔴 **SELL/TAKE PROFIT {r['ticker']}** @ ${r['price']} — "
                      f"RSI {r['rsi14']} 超买, 置信度 {r['confidence']}")
        md.append("")
    md.append("---")
    md.append("*Powered by QuantDinger API + AgenticTendies | 每15分钟自动更新*")

    # --- WRITE TO 3 CRON PATHS ---
    out_paths = [
        f"/opt/data/cron_output/{JOB_ID}/portfolio-research-{tsf}.md",
        f"/opt/data/.cron/output/{JOB_ID}/portfolio-research-{tsf}.md",
        f"/opt/data/home/./cron/output/{JOB_ID}/portfolio-research-{tsf}.md",
    ]
    content = "\n".join(md)
    for p in out_paths:
        try:
            os.makedirs(os.path.dirname(p), exist_ok=True)
            with open(p, "w") as f: f.write(content)
            print(f"SAVED: {p}")
        except Exception as e:
            print(f"FAIL {p}: {e}", file=sys.stderr)

    # Discord short message
    discord_short = f"📊 *AI/基建扫描* — {ts}\n"
    discord_short += f"RSI均={avg_rsi:.1f} | 超买={ob} 超卖={os_} | {sentiment}\n\n"
    for i, r in enumerate(ranked[:3], 1):
        sig = {"BUY": "🟢", "SELL": "🔴", "HOLD": "🟡"}.get(r["signal"], "·")
        discord_short += (f"{sig} **{r['ticker']}** ${r['price']} "
                          f"RSI {r['rsi14']} → {r['signal']} (conf {r['confidence']})\n")
    gld_px = fetch_price('GLD') or 0
    tsm_px = fetch_price('TSM') or 0
    discord_short += (f"\n💼 GLD×4 ${gld_px:.2f} | TSM×5 ${tsm_px:.2f}\n")
    if ob >= 3:
        discord_short += "⚠️ 板块超买，DELL/SMCI/AMD 优先止盈"
    try:
        msg_path = f"/opt/hermes/cron/output/{JOB_ID}/discord_msg_{tsf}.txt"
        os.makedirs(os.path.dirname(msg_path), exist_ok=True)
        with open(msg_path, "w") as f: f.write(discord_short)
        print(f"DISCORD MSG: {msg_path}")
    except Exception as e:
        print(f"discord msg fail: {e}", file=sys.stderr)

    print("---REPORT---")
    print(content)
    return content


if __name__ == "__main__":
    main()
