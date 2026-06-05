"""Portfolio research cron — fetch QuantDinger klines, compute indicators, write markdown report.

Usage (from anywhere):
    cd /opt/data/agentictendies && \
    PYTHONPATH=/opt/data/agentictendies \
    .venv/bin/python /opt/data/skills/portfolio-research-cron-quantdinger/scripts/run_research.py

Output:
    ~/.cron/output/f2f177230acb/portfolio-research-YYYYMMDD-HHMM.md
    ~/.cron/output/f2f177230acb/portfolio-research-latest.md (mirror)

Why the venv + PYTHONPATH dance:
- `agentictendies.core.indicators` is the single source of truth for RSI/SMA/ATR/EMA.
- Importing it triggers `core/__init__.py` -> `ingestion.py` -> `import yfinance`,
  so the venv (which has yfinance + pandas + numpy) is mandatory.
- The system `python3` has none of those, and the `execute_code` sandbox
  is even more minimal (no numpy). Do not try to run this from a
  sandbox or system python.

Why Series, not lists:
- `calculate_rsi` calls `prices.diff()` -> pandas-only.
- NaN checks via `if v is not None` will choke on a Series
  ("truth value of a Series is ambiguous"). Use a Series-aware
  `last_valid()` helper.
"""
import os
import sys
import json
import urllib.request
import pandas as pd
import numpy as np
from datetime import datetime, timezone

# Import news fetcher from same dir
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fetch_news import fetch_all_news

TOKEN = os.environ.get(
    "QUANTDINGER_TOKEN",
    "qd_agent_TWSkB8spR49Kuccw_WMEaVl0L18YyVQG6PaVt6OJ7nM",
)
BASE = os.environ.get("QUANTDINGER_BASE", "http://localhost:8888")

TICKERS = ["VRT", "SMCI", "PLTR", "AMD", "NVDA", "COIN", "DELL", "SPY"]
WATCHLIST = ["VRT", "SMCI", "PLTR", "AMD", "NVDA", "COIN", "DELL"]


def get_klines(symbol, limit=200):
    req = urllib.request.Request(
        f"{BASE}/api/agent/v1/klines?market=USStock&symbol={symbol}"
        f"&timeframe=1d&limit={limit}"
    )
    req.add_header("Authorization", f"Bearer {TOKEN}")
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            resp = json.loads(r.read())
        if resp.get("code") == 0:
            return resp.get("data", {}).get("klines", [])
    except Exception as e:
        print(f"ERR {symbol}: {e}")
    return []


def last_valid(arr):
    """Series-safe last non-null value. Works on pandas Series and Python lists."""
    if arr is None:
        return None
    if hasattr(arr, "iloc"):
        if len(arr) == 0:
            return None
        for v in arr.iloc[::-1]:
            if v is not None and not (isinstance(v, float) and np.isnan(v)):
                return float(v)
        return None
    if not arr:
        return None
    for v in reversed(arr):
        if v is not None:
            return v
    return None


def stochastic_k(high, low, close, k_period=14, d_period=3):
    if len(close) < k_period + d_period:
        return None, None
    if hasattr(close, "tolist"):
        close_list, high_list, low_list = close.tolist(), high.tolist(), low.tolist()
    else:
        close_list, high_list, low_list = list(close), list(high), list(low)
    fast_k = []
    for i in range(k_period - 1, len(close_list)):
        hh = max(high_list[i - k_period + 1: i + 1])
        ll = min(low_list[i - k_period + 1: i + 1])
        fast_k.append(50.0 if hh == ll else (close_list[i] - ll) / (hh - ll) * 100)
    if len(fast_k) < d_period:
        return fast_k[-1] if fast_k else None, None
    smooth_k = sum(fast_k[-d_period:]) / d_period
    d_vals = [
        sum(fast_k[i - d_period + 1: i + 1]) / d_period
        for i in range(d_period - 1, len(fast_k))
    ]
    return smooth_k, d_vals[-1] if d_vals else None


def analyze(ticker, klines):
    if not klines or len(klines) < 60:
        return None
    closes = pd.Series([k["close"] for k in klines])
    highs = pd.Series([k["high"] for k in klines])
    lows = pd.Series([k["low"] for k in klines])
    vols = pd.Series([k["volume"] for k in klines])

    from agentictendies.core.indicators import (
        calculate_rsi, calculate_sma, calculate_atr, calculate_ema,
    )

    rsi = calculate_rsi(closes, 14)
    sma20 = calculate_sma(closes, 20)
    sma50 = calculate_sma(closes, 50)
    ema20 = calculate_ema(closes, 20)
    atr = calculate_atr(highs, lows, closes, 14)

    last = float(closes.iloc[-1])
    prev = float(closes.iloc[-2]) if len(closes) >= 2 else last
    day_pct = (last - prev) / prev * 100

    rsi_last = last_valid(rsi)
    sma20_last = last_valid(sma20)
    sma50_last = last_valid(sma50)
    ema20_last = last_valid(ema20)
    atr_last = last_valid(atr)

    stoch_k, stoch_d = stochastic_k(highs, lows, closes, 14, 3)

    if len(vols) >= 25:
        recent_vol = sum(vols.iloc[-5:].tolist()) / 5
        base_vol = sum(vols.iloc[-25:-5].tolist()) / 20
        vol_ratio = recent_vol / base_vol if base_vol > 0 else 1.0
    else:
        vol_ratio = 1.0

    # Signal logic (priority order)
    signal = "HOLD"
    reasons = []
    if rsi_last is not None:
        if rsi_last < 40:
            signal = "BUY"
            reasons.append(f"RSI {rsi_last:.1f}超卖")
        elif rsi_last > 70:
            signal = "SELL"
            reasons.append(f"RSI {rsi_last:.1f}超买")
        elif 40 <= rsi_last <= 55 and sma20_last is not None and last > sma20_last:
            signal = "BUY"
            reasons.append(f"RSI {rsi_last:.1f}+价>SMA20")
        else:
            reasons.append(f"RSI {rsi_last:.1f}中性")

    if sma20_last is not None and sma50_last is not None and sma20_last > sma50_last:
        if signal in ("BUY", "HOLD"):
            signal = "BUY*"
        reasons.append("SMA20>SMA50 黄金交叉")
    reason = "; ".join(reasons) if reasons else "无信号"

    # Confidence score
    score = 0.0
    if rsi_last is not None:
        score += min(abs(rsi_last - 50), 30)
    if sma20_last and sma50_last and sma50_last > 0:
        score += abs((sma20_last - sma50_last) / sma50_last) * 100 * 1.5
    if signal in ("BUY", "BUY*"):
        score += 10
    elif signal == "SELL":
        score += 8
    if stoch_k is not None and (stoch_k > 80 or stoch_k < 20):
        score += 5

    return {
        "ticker": ticker,
        "price": round(last, 2),
        "day_pct": round(day_pct, 2),
        "rsi": round(rsi_last, 1) if rsi_last else None,
        "sma20": round(sma20_last, 2) if sma20_last else None,
        "sma50": round(sma50_last, 2) if sma50_last else None,
        "ema20": round(ema20_last, 2) if ema20_last else None,
        "atr": round(atr_last, 2) if atr_last else None,
        "stoch_k": round(stoch_k, 1) if stoch_k is not None else None,
        "stoch_d": round(stoch_d, 1) if stoch_d is not None else None,
        "vol_ratio": round(vol_ratio, 2),
        "signal": signal,
        "reason": reason,
        "score": round(score, 2),
    }


def sig_emoji(s):
    return {"BUY*": "🟢 BUY*", "BUY": "🟢 BUY", "SELL": "🔴 SELL"}.get(s, "🟡 HOLD")


def render_table(headers: list[str], rows: list[list[str]], col_aligns: list[str] | None = None) -> list[str]:
    """Render a Discord-friendly table inside a code block using box-drawing chars.

    Discord does NOT render markdown pipe-tables. They show as raw
    `| 1 | AMD |...|`. To get a real monospace-aligned table on every
    Discord client (desktop + mobile), we wrap the table in a triple-
    backtick code block and use Unicode box-drawing characters
    (┌ ─ ┬ │ ├ ┤ └ ┴ ┼) for the borders.

    col_aligns: list of 'l'/'r'/'c' per column. Default 'l' for all.
    Returns a list of strings (one per line) — caller joins with newlines
    and embeds in ``` fences.
    """
    n_cols = len(headers)
    if not col_aligns:
        col_aligns = ['l'] * n_cols

    # Compute column widths
    widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            if i < n_cols:
                # Strip ANSI/markdown for width calc; emoji count as 2 chars in monospace
                # (rough heuristic: most emoji = 2 cols)
                cell_w = sum(2 if ord(c) > 0x2700 else 1 for c in str(cell))
                widths[i] = max(widths[i], cell_w)

    def pad(cell: str, w: int, align: str) -> str:
        s = str(cell)
        cell_w = sum(2 if ord(c) > 0x2700 else 1 for c in s)
        gap = w - cell_w
        if gap <= 0:
            return s
        if align == 'r':
            return ' ' * gap + s
        if align == 'c':
            lpad = gap // 2
            return ' ' * lpad + s + ' ' * (gap - lpad)
        return s + ' ' * gap  # default 'l'

    h_sep = '─'  # horizontal line char
    v_sep = '│'
    cross_t = '┼'
    cross_b = '┴'
    cross_l = '├'
    cross_r = '┤'
    top_l = '┌'
    top_r = '┐'
    bot_l = '└'
    bot_r = '┘'
    top_t = '┬'
    bot_t = '┬'  # bottom uses ┬ rotated (we use ┴ via cross_b)

    top = top_l + top_t.join('─' * (w + 2) for w in widths) + top_r
    mid = cross_l + cross_t.join('─' * (w + 2) for w in widths) + cross_r
    bot = bot_l + cross_b.join('─' * (w + 2) for w in widths) + bot_r

    head_line = v_sep + v_sep.join(' ' + pad(headers[i], widths[i], col_aligns[i]) + ' ' for i in range(n_cols)) + v_sep
    body = []
    for row in rows:
        body.append(v_sep + v_sep.join(' ' + pad(row[i] if i < len(row) else '', widths[i], col_aligns[i]) + ' ' for i in range(n_cols)) + v_sep)

    return [top, head_line, mid] + body + [bot]


def note_for(r):
    """Build a Chinese per-ticker note from live indicator values.

    Avoids hardcoded commentary: QuantDinger klines are a static
    snapshot, so any canned day%/price/RSI string will be wrong on
    most runs. Build the note from the freshly-computed r dict.
    """
    parts = []
    rsi, sk, day, vr = r["rsi"], r["stoch_k"], r["day_pct"], r["vol_ratio"]
    sma20, sma50 = r["sma20"], r["sma50"]
    if rsi is not None:
        if rsi < 30:   parts.append(f"RSI {rsi:.1f}深度超卖")
        elif rsi < 40: parts.append(f"RSI {rsi:.1f}超卖")
        elif rsi > 80: parts.append(f"RSI {rsi:.1f}极度超买")
        elif rsi > 70: parts.append(f"RSI {rsi:.1f}超买")
        else:          parts.append(f"RSI {rsi:.1f}中性")
    if sk is not None:
        if sk < 20:   parts.append(f"随机 {sk:.1f}深度超卖")
        elif sk > 80: parts.append(f"随机 {sk:.1f}超买")
    if day is not None:
        if abs(day) >= 10: parts.append(f"单日 {day:+.2f}% 异常波动")
        elif abs(day) >= 5: parts.append(f"单日 {day:+.2f}% 较大波动")
    if vr is not None and vr >= 2.0:
        parts.append(f"量{vr:.2f}倍")
    if sma20 is not None and sma50 is not None:
        if sma20 > sma50:
            parts.append("SMA20>SMA50 趋势向上")
        elif sma20 < sma50:
            parts.append("SMA20<SMA50 趋势走弱")
    base = r["signal"]
    if base.startswith("BUY"):
        action = "**BUY信号** — 关注分批建仓"
    elif base == "SELL":
        action = "**SELL信号** — 建议减仓/止盈"
    else:
        action = "**HOLD** — 持有观察"
    return f"{action}。{'; '.join(parts) if parts else '无显著指标'}。"


NOTES = {}  # DEPRECATED: never hardcode per-ticker commentary. QuantDinger
              # klines are a static snapshot, not live, so any canned
              # day%/price/RSI string will be wrong on most runs and
              # mislead the user. The per-ticker block below now builds
              # notes dynamically via note_for(r).


# --- News block --------------------------------------------------------

# Tagging priority: a higher rank = more important to surface in the report.
# Macro keyword tags (Fed/AI/Gold/Taiwan/Crypto) are bundled in fetch_news.
NEWS_TICKER_PRIORITY = {
    # Holdings first — news about these is actionable
    "GLD": 100, "TSM": 100,
    # Watchlist next
    "VRT": 90, "SMCI": 90, "PLTR": 90, "AMD": 90,
    "NVDA": 90, "COIN": 90, "DELL": 90,
    # Macro / sector
    "AI": 70, "Fed": 70, "Gold": 70, "Taiwan": 70, "Crypto": 70,
    # Generic
    "MACRO": 50, "SPY": 40,
}
MAX_NEWS_IN_REPORT = 7  # cap to keep the full report under Discord 4000-char limit
                        # (cron scheduler truncates at ~4000; we want the
                        # technical-signal table + portfolio table to survive
                        # even if the news block has to be trimmed.)


def _fmt_news_age(published: datetime | None) -> str:
    if published is None:
        return "      "
    delta = datetime.now(timezone.utc) - published
    mins = int(delta.total_seconds() // 60)
    if mins < 60:
        return f"{mins}m ago"
    hours = mins // 60
    if hours < 24:
        return f"{hours}h ago"
    return f"{hours // 24}d ago"


def render_news_block(items: list[dict]) -> list[str]:
    """Build a compact markdown news block. Cap to MAX_NEWS_IN_REPORT."""
    if not items:
        return ["", "## 📰 相关新闻 (News — last 12h)", "", "_no recent headlines (RSS unavailable or rate-limited)_", ""]

    # Sort by priority desc, then by published desc. Tickers not in the
    # priority dict get rank 0.
    def rank_key(it):
        t = it.get("ticker", "MACRO")
        prio = NEWS_TICKER_PRIORITY.get(t, 0)
        ts = it.get("published") or datetime.min.replace(tzinfo=timezone.utc)
        # Negative prio first (sort high-priority first), then newest
        return (-prio, -ts.timestamp())

    sorted_items = sorted(items, key=rank_key)
    top = sorted_items[:MAX_NEWS_IN_REPORT]

    lines = ["", "## 📰 相关新闻 (News — last 12h, by priority)", ""]
    for it in top:
        ticker = it.get("ticker", "?")
        age = _fmt_news_age(it.get("published"))
        title = it["title"].replace("|", "\\|")  # escape pipe to keep table safe
        link = it.get("link", "")
        # Inline link syntax (Discord-friendly preview via OpenGraph)
        lines.append(f"- **[{ticker}]** {age} — [{title}]({link})")
    lines.append("")
    return lines


def main():
    raw = {t: get_klines(t, 200) for t in TICKERS}
    results = {t: r for t in TICKERS if (r := analyze(t, raw.get(t, [])))}

    # Fetch news for watchlist only (portfolio GLD/TSM removed 2026-06-04 per user request).
    # Failures must not break the report — wrap in try/except.
    news_items: list[dict] = []
    try:
        news_items = fetch_all_news(WATCHLIST, max_age_hours=12, include_macros=True)
    except Exception as e:
        print(f"WARN fetch_news failed: {e}", flush=True)
        news_items = []

    ranked = sorted([results[t] for t in WATCHLIST if t in results], key=lambda x: x["score"], reverse=True)

    now = datetime.now(timezone.utc)
    date_str = now.strftime("%Y-%m-%d %H:%M")
    file_stamp = now.strftime("%Y%m%d-%H%M")

    spy = results.get("SPY", {})
    spy_price = spy.get("price")
    spy_sma50 = spy.get("sma50")
    if spy_price and spy_sma50:
        regime = "BULL 🐂" if spy_price > spy_sma50 else "BEAR 🐻"
        spy_str = f"SPY ${spy_price:.2f} | SMA50 ${spy_sma50:.2f} | {regime}"
    else:
        spy_str = "SPY N/A"

    lines = [
        f"# 📊 AI/基建股票扫描 — {date_str} UTC",
        "",
        "## 🌍 市场背景 (Market Context)",
        f"- **{spy_str}**",
        "- VIX: N/A (QuantDinger 不提供)",
        # Build market-context sentence from SPY indicators, not canned text
        f"- 整体趋势: " + (
            "SPY 超买 (RSI>70), 板块情绪偏热, 短线注意获利回吐"
            if spy.get("rsi") and spy["rsi"] > 70
            else "SPY 中性偏强, 趋势仍向上"
            if spy.get("sma20") and spy.get("sma50") and spy["sma20"] > spy["sma50"]
            else "SPY 趋势走弱, 谨慎加仓"
        ),
        "",
    ]
    # News block is added to the END of the report (after the footer
    # marker) so that if the cron scheduler truncates to Discord's
    # 4096-char limit, the technical signal table, portfolio P&L, and
    # per-ticker notes survive first. News is a nice-to-have complement;
    # signal+positions are essential.
    lines += [
        "",
        "## 🏆 信号排名 (Ranked Signals)",
        "",
        "```",  # start code block for table
    ]
    # Build ranking table rows
    rank_rows = []
    for i, r in enumerate(ranked, 1):
        rank_rows.append([
            str(i),
            f"**{r['ticker']}**",
            f"${r['price']}",
            f"{r['day_pct']:+.2f}%",
            f"{r['rsi']}",
            f"${r['sma20']}",
            f"${r['sma50']}",
            f"{r['stoch_k']}",
            f"{r['vol_ratio']}",
            sig_emoji(r['signal']),
            f"{r['score']}",
        ])
    # Right-align numeric columns (rank, price, day%, RSI, prices, score)
    rank_aligns = ['r', 'l', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'l', 'r']
    table_lines = render_table(
        ['#', 'Ticker', 'Price', 'Day%', 'RSI', 'SMA20', 'SMA50', 'StochK', 'VolR', 'Signal', 'Score'],
        rank_rows,
        rank_aligns,
    )
    lines += table_lines
    lines += ["```"]  # end code block

    lines += ["", "## 📝 个股点评 (Per-Ticker Notes)", ""]
    for t in WATCHLIST:
        if t in results:
            r = results[t]
            lines.append(f"- **{t}** ({r['signal']}, score {r['score']}): {note_for(r)}")

    lines += [
        "",
        "## ⚠️ 风险提示",
        # Dynamic risk bullets built from current run's indicator values
        *(["- ⚠️ 超买区 (RSI>70): " + ", ".join(
              t for t in WATCHLIST
              if t in results and results[t]["rsi"] is not None and results[t]["rsi"] > 70
          ) + " — 短线注意获利回吐"] if any(
              t in results and results[t]["rsi"] is not None and results[t]["rsi"] > 70
              for t in WATCHLIST
          ) else []),
        *(["- 💚 超卖区 (RSI<40): " + ", ".join(
              t for t in WATCHLIST
              if t in results and results[t]["rsi"] is not None and results[t]["rsi"] < 40
          ) + " — 关注反弹机会"] if any(
              t in results and results[t]["rsi"] is not None and results[t]["rsi"] < 40
              for t in WATCHLIST
          ) else []),
        *(["- 📈 趋势向上 (SMA20>SMA50): " + ", ".join(
              t for t in WATCHLIST
              if t in results and results[t]["sma20"] is not None
              and results[t]["sma50"] is not None
              and results[t]["sma20"] > results[t]["sma50"]
          )] if any(
              t in results and results[t]["sma20"] is not None
              and results[t]["sma50"] is not None
              and results[t]["sma20"] > results[t]["sma50"]
              for t in WATCHLIST
          ) else []),
        "- ⚠️ 数据源为 QuantDinger klines 快照（非实时报价），单日涨跌幅>10% 可能为数据异常",
        "",
        "---",
        f"*生成时间: {date_str} UTC | 数据源: QuantDinger API + AgenticTendies indicators + Yahoo Finance RSS*",
        f"*报告路径: ~/./cron/output/f2f177230acb/portfolio-research-{file_stamp}.md*",
        f"*新闻条数: {len(news_items)} (12h 窗口, 按 ticker 优先级排序; 最多展示 {MAX_NEWS_IN_REPORT})*",
    ]
    # News block appended at the very end so cron scheduler truncation
    # (Discord 4096-char) drops news first, preserving signal table +
    # portfolio + per-ticker notes. News headlines are accessible in
    # the saved .md file even if truncated in chat.
    lines += render_news_block(news_items)
    md = "\n".join(lines)

    out_dir = os.path.expanduser("~/.cron/output/f2f177230acb")
    os.makedirs(out_dir, exist_ok=True)
    out_path = f"{out_dir}/portfolio-research-{file_stamp}.md"
    with open(out_path, "w") as f:
        f.write(md)
    with open(f"{out_dir}/portfolio-research-latest.md", "w") as f:
        f.write(md)

    print(f"WROTE: {out_path}  ({len(md)} chars)")
    print(md)


if __name__ == "__main__":
    main()
