"""Portfolio research cron — 15-min sweep.

Drop-in script for a cron job that scans a fixed ticker list via QuantDinger,
computes technicals with the local AgenticTendies framework, prices current
holdings (with klines fallback), ranks by composite score, and writes a
markdown report to ~/./cron/output/<JOB_ID>/.

Environment:
    QUANTDINGER_TOKEN  Bearer token (required)
    QUANTDINGER_BASE   defaults to http://localhost:8888
    CRON_JOB_ID        output subdirectory, e.g. f2f177230acb

Reproduce-with-modifications: change TICKERS, PORTFOLIO_HOLDINGS, or the
scoring weights in `score()` for a different strategy.
"""
import json
import os
import sys
import urllib.request
from datetime import datetime

import numpy as np
import pandas as pd

sys.path.insert(0, "/opt/data/agentictendies")
from agentictendies.core.indicators import (
    calculate_rsi, calculate_sma, calculate_atr,
)

TOKEN = os.environ["QUANTDINGER_TOKEN"]
BASE = os.environ.get("QUANTDINGER_BASE", "http://localhost:8888")
JOB_ID = os.environ.get("CRON_JOB_ID", "f2f177230acb")

TICKERS = ["VRT", "SMCI", "PLTR", "AMD", "NVDA", "COIN", "DELL"]
PORTFOLIO_HOLDINGS = [
    {"ticker": "GLD", "shares": 4, "avg_cost": 588.79},
    {"ticker": "TSM", "shares": 5, "avg_cost": 563.93},
]
NAMES = {
    "VRT": "Vertiv (数据中心电力/制冷)", "SMCI": "Super Micro (AI 服务器)",
    "PLTR": "Palantir (AI 数据分析)", "AMD": "AMD (AI 加速器)",
    "NVDA": "NVIDIA (AI 芯片龙头)", "COIN": "Coinbase (加密交易)",
    "DELL": "Dell (AI 服务器)", "GLD": "SPDR Gold Shares", "TSM": "TSMC ADR",
}


# ---------- API helpers ----------

def fetch_klines(symbol, limit=120):
    req = urllib.request.Request(
        f"{BASE}/api/agent/v1/klines?market=USStock&symbol={symbol}&timeframe=1d&limit={limit}"
    )
    req.add_header("Authorization", f"Bearer {TOKEN}")
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read())


def fetch_price(symbol):
    req = urllib.request.Request(f"{BASE}/api/agent/v1/price?market=USStock&symbol={symbol}")
    req.add_header("Authorization", f"Bearer {TOKEN}")
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read())


def to_df(payload):
    if not isinstance(payload, dict):
        raise ValueError(f"unexpected payload type: {type(payload)}")
    data = payload.get("data", payload)
    rows = None
    if isinstance(data, dict):
        for k in ("klines", "candles", "data", "result"):
            v = data.get(k)
            if isinstance(v, list) and v:
                rows = v
                break
    elif isinstance(data, list):
        rows = data
    if not rows:
        raise ValueError(f"no klines rows: {str(payload)[:200]}")
    df = pd.DataFrame(rows)
    col_map = {}
    for c in df.columns:
        cl = str(c).lower()
        col_map[c] = {"time": "ts", "timestamp": "ts", "ts": "ts", "date": "ts",
                      "open": "open", "high": "high", "low": "low",
                      "close": "close", "volume": "volume"}.get(cl, c)
    df = df.rename(columns=col_map)
    missing = {"open", "high", "low", "close", "volume"} - set(df.columns)
    if missing:
        if df.shape[1] >= 6:
            df = df.iloc[:, :6]
            df.columns = ["ts", "open", "high", "low", "close", "volume"]
        else:
            raise ValueError(f"missing cols {missing}")
    for c in ("open", "high", "low", "close", "volume"):
        df[c] = pd.to_numeric(df[c], errors="coerce")
    if "ts" in df.columns and np.issubdtype(df["ts"].dtype, np.number) and df["ts"].max() > 1e12:
        df["ts"] = pd.to_datetime(df["ts"], unit="s")
    return df


# ---------- Indicators + scoring ----------

def stochastic_k(df, k_period=14, smooth=3):
    lo = df["low"].rolling(k_period).min()
    hi = df["high"].rolling(k_period).max()
    k = (df["close"] - lo) / (hi - lo) * 100
    return k.rolling(smooth).mean()


def has(v):
    return v is not None and not (isinstance(v, float) and np.isnan(v))


def analyze(symbol):
    try:
        df = to_df(fetch_klines(symbol))
    except Exception as e:
        return {"symbol": symbol, "error": str(e)[:120]}
    if len(df) < 30:
        return {"symbol": symbol, "error": f"only {len(df)} rows"}
    df = df.sort_values("ts").reset_index(drop=True)
    df["rsi14"] = calculate_rsi(df["close"], 14)
    df["sma20"] = calculate_sma(df["close"], 20)
    df["sma50"] = calculate_sma(df["close"], 50)
    df["atr14"] = calculate_atr(df["high"], df["low"], df["close"], 14)
    df["stoch_k"] = stochastic_k(df)
    df["vol_ratio"] = df["volume"] / df["volume"].rolling(20).mean()

    last, prev = df.iloc[-1], df.iloc[-2]
    rsi, price = float(last["rsi14"]), float(last["close"])
    sma20 = float(last["sma20"]) if has(last["sma20"]) else None
    sma50 = float(last["sma50"]) if has(last["sma50"]) else None
    stoch = float(last["stoch_k"]) if has(last["stoch_k"]) else None
    vol_ratio = float(last["vol_ratio"]) if has(last["vol_ratio"]) else None

    signals, conf = [], 0.0
    if rsi < 40: signals.append("RSI超卖<40 → BUY"); conf += 35
    elif rsi > 70: signals.append("RSI超买>70 → SELL"); conf -= 35
    elif 40 <= rsi <= 55 and sma20 and price > sma20:
        signals.append("RSI 40-55 + 价格>SMA20 → BUY"); conf += 20
    if has(sma20) and has(sma50):
        if sma20 > sma50: signals.append("SMA20>SMA50 黄金交叉 → 趋势看多"); conf += 25
        else: signals.append("SMA20<SMA50 死叉 → 趋势偏空"); conf -= 20
    if stoch is not None:
        if stoch < 20: signals.append("Stochastic<20 超卖"); conf += 10
        elif stoch > 80: signals.append("Stochastic>80 超买"); conf -= 10
    if vol_ratio is not None and vol_ratio > 1.5:
        signals.append(f"放量 {vol_ratio:.1f}x")

    rsi_dist = abs(rsi - 50)
    trend_pct = (abs(sma20 - sma50) / sma50 * 100) if has(sma20) and has(sma50) else 0.0
    score = max(0, min(100, conf + rsi_dist * 0.5 + trend_pct * 2 + 25))
    chg_1d = (price - float(prev["close"])) / float(prev["close"]) * 100

    return {"symbol": symbol, "price": price, "rsi14": rsi, "sma20": sma20,
            "sma50": sma50, "stoch_k": stoch, "vol_ratio": vol_ratio,
            "chg_1d_pct": chg_1d, "signals": signals, "confidence": round(conf, 1),
            "score": round(score, 1), "trend_strength_pct": round(trend_pct, 2)}


def fetch_portfolio_price(symbol):
    try:
        data = fetch_price(symbol).get("data", {})
        for k in ("price", "last", "close", "regularMarketPrice"):
            v = data.get(k)
            if v is not None and isinstance(v, (int, float)) and v > 0:
                return float(v)
    except Exception:
        pass
    try:
        df = to_df(fetch_klines(symbol, limit=5))
        if len(df):
            return float(df["close"].iloc[-1])
    except Exception:
        pass
    return None


# ---------- Formatting ----------

def fmt(v, d=2, prefix="$"):
    return "n/a" if not has(v) else f"{prefix}{v:.{d}f}"


def fmt_pct(v, d=2):
    return "n/a" if not has(v) else f"{v:.{d}f}%"


# ---------- Report ----------

def main():
    results = [analyze(t) for t in TICKERS]
    price_map = {r["symbol"]: r.get("price") for r in results if "error" not in r}
    for h in PORTFOLIO_HOLDINGS:
        if h["ticker"] not in price_map:
            price_map[h["ticker"]] = fetch_portfolio_price(h["ticker"])

    valid = sorted([r for r in results if "error" not in r], key=lambda x: x["score"], reverse=True)
    ranked = valid + [r for r in results if "error" in r]

    ts = datetime.now()
    ts_short, ts_human = ts.strftime("%Y%m%d-%H%M"), ts.strftime("%Y-%m-%d %H:%M")

    L = [f"# 投资组合研究报告 / Portfolio Research Report", "",
         f"**生成时间 / Generated:** {ts_human} (cron run, every 15min)",
         f"**主题 / Theme:** AI / 基础设施 (AI / Infrastructure)",
         f"**数据源 / Source:** QuantDinger 60-day daily klines", "",
         "## 📊 排名 / Ranking (按置信度分数)", "",
         "| Rank | Ticker | Score | RSI(14) | Price | SMA20 | SMA50 | Trend% | 1d Δ% | Signal |",
         "|---:|:---|---:|---:|---:|---:|---:|---:|---:|:---|"]
    for i, r in enumerate(ranked, 1):
        if "error" in r:
            L.append(f"| {i} | **{r['symbol']}** | ERR | — | — | — | — | — | — | {r['error']} |")
            continue
        sig = " / ".join(r["signals"][:2]) if r["signals"] else "中性"
        emoji = "🟢" if r["confidence"] > 20 else ("🔴" if r["confidence"] < -10 else "🟡")
        L.append(f"| {i} | **{r['symbol']}** | {r['score']:.1f} | {r['rsi14']:.1f} | "
                 f"{fmt(r['price'])} | {fmt(r['sma20'])} | {fmt(r['sma50'])} | "
                 f"{fmt_pct(r['trend_strength_pct'])} | {r['chg_1d_pct']:+.2f}% | {emoji} {sig} |")

    L += ["", "## 🔍 中文解读 / Chinese Commentary", ""]
    for r in valid[:3]:
        direction = "偏多" if r["confidence"] > 10 else ("偏空" if r["confidence"] < -10 else "震荡")
        L.append(f"**{r['symbol']}** ({NAMES.get(r['symbol'], r['symbol'])}) — 当前 {fmt(r['price'])}，"
                 f"RSI {r['rsi14']:.1f}，1日 {r['chg_1d_pct']:+.2f}%。信号: {direction}。")
        for s in r["signals"]:
            L.append(f"  - {s}")
        L.append("")

    L += ["## 💼 当前持仓 / Current Holdings (TD Direct 41HHH9A)", "",
          "| Ticker | Shares | Avg Cost | Current $ | Mkt Value | Unrealized |",
          "|:---|---:|---:|---:|---:|---:|"]
    total_mv = total_cost = 0.0
    for h in PORTFOLIO_HOLDINGS:
        px = price_map.get(h["ticker"])
        if px:
            mv = h["shares"] * px
            cost = h["shares"] * h["avg_cost"]
            upl = mv - cost
            total_mv, total_cost = total_mv + mv, total_cost + cost
            L.append(f"| {h['ticker']} | {h['shares']} | {fmt(h['avg_cost'])} | {fmt(px)} | "
                     f"${mv:,.2f} | {upl:+,.2f} ({(px/h['avg_cost']-1)*100:+.2f}%) |")
        else:
            L.append(f"| {h['ticker']} | {h['shares']} | {fmt(h['avg_cost'])} | n/a | n/a | n/a |")
    if total_cost > 0:
        L.append(f"| **合计** | — | — | — | **${total_mv:,.2f}** | "
                 f"**{total_mv-total_cost:+,.2f} ({(total_mv/total_cost-1)*100:+.2f}%)** |")
    L.append("")

    oversold = [r["symbol"] for r in valid if r["rsi14"] < 40]
    overbought = [r["symbol"] for r in valid if r["rsi14"] > 70]
    golden = [r["symbol"] for r in valid if has(r["sma20"]) and has(r["sma50"]) and r["sma20"] > r["sma50"]]
    death = [r["symbol"] for r in valid if has(r["sma20"]) and has(r["sma50"]) and r["sma20"] < r["sma50"]]
    L += ["## ⚠️ 关注 / Watchlist Notes", ""]
    if oversold:  L.append(f"**超卖 (RSI<40):** {', '.join(oversold)}")
    if overbought: L.append(f"**超买 (RSI>70):** {', '.join(overbought)}")
    if golden:    L.append(f"**Golden Cross (SMA20>SMA50):** {', '.join(golden)}")
    if death:     L.append(f"**Death Cross (SMA20<SMA50):** {', '.join(death)}")
    L.append("")

    buys = [r for r in valid if r["confidence"] > 20]
    sells = [r for r in valid if r["confidence"] < -15]
    L += ["## 🎯 操作建议 / Action Items", ""]
    if buys:
        L.append("**考虑建仓/加仓 (Confidence > 20):**")
        for r in buys[:3]:
            L.append(f"- {r['symbol']} @ {fmt(r['price'])} (RSI {r['rsi14']:.1f}, score {r['score']:.1f})")
    if sells:
        L.append("**考虑减仓/止盈 (Confidence < -15):**")
        for r in sells[:3]:
            L.append(f"- {r['symbol']} @ {fmt(r['price'])} (RSI {r['rsi14']:.1f}, score {r['score']:.1f})")
    if not buys and not sells:
        L.append("当前无明确信号，建议持有观望。")
    L += ["", "---",
          "_自动生成 / Auto-generated by cron job • 15-min cadence • AgenticTendies + QuantDinger_"]

    md = "\n".join(L)
    out_dir = os.path.expanduser(f"~/./cron/output/{JOB_ID}")
    os.makedirs(out_dir, exist_ok=True)
    for name in (f"portfolio-research-{ts_short}.md", "portfolio-research-latest.md"):
        with open(os.path.join(out_dir, name), "w") as f:
            f.write(md)

    print(f"OK: {len(valid)}/{len(TICKERS)} research + "
          f"{sum(1 for h in PORTFOLIO_HOLDINGS if price_map.get(h['ticker']))}/"
          f"{len(PORTFOLIO_HOLDINGS)} holdings priced")


if __name__ == "__main__":
    main()
