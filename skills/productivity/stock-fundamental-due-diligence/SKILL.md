---
name: stock-fundamental-due-diligence
description: "Deep qualitative/fundamental due diligence on a single US-listed equity — pull primary SEC filings (10-K/10-Q/8-K/13F), peer multiples, earnings call transcripts, M&A timeline, technicals, and synthesize into a decision-tree research note. Use when user asks to 'dig into', 'research', 'analyze', or 'DD' a specific stock (not for multi-ticker scans — use portfolio-research instead). Output: markdown note in /opt/data/notes/{TICKER}-{YYYY-MM-DD}.md + a 5-bullet decision summary in chat."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [stocks, fundamentals, due-diligence, sec-filings, peer-comparison, research]
    related_skills: [portfolio-research, youtube-content]
---

## When to use this skill

Use when the user asks for **deep research on a specific single ticker** — "dig into VRT", "research NVDA", "is MU a buy right now", "compare VRT to peers". Triggers include:

- "dig into [TICKER]" / "research [TICKER]" / "analyze [TICKER]"
- "is [TICKER] a buy/add/sell?"
- "[TICKER] earnings preview" / "[TICKER] 财报分析"
- Single-ticker deep DD requested

**Also use when the user names a product / company / ticker that may not exist or be misspelled** (e.g. "nvidia rtx spark", "apple NTX"). The right move is to verify against SEC EDGAR full-text + Yahoo Finance symbol lookup, then write a note that documents what was found (or what the most likely real name is). Do NOT refuse to research just because the literal string isn't a real product — try the obvious close variants (RTX↔DGX, GB200↔GB300, M3↔M4) before giving up. Verified 2026-06-02: stangg said "nvidia rtx spark" → literal lookup returned 0 hits in SEC EDGAR + Yahoo; swapping "RTX" for "DGX" (NVIDIA's two machine-learning prefixes) found "DGX Spark" with 10 SEC filings; Q3 FY26 press release confirmed "Began shipping NVIDIA DGX Spark, the world's smallest AI supercomputer" + $3,999 + GB10 + 1 PFLOPS FP4.

**Do NOT use for**: multi-ticker scans (use `portfolio-research`), quick price quote, or pure technicals-only scans.

## Difference from `portfolio-research`

| Aspect | portfolio-research | stock-fundamental-due-diligence |
|--------|-------------------|--------------------------------|
| Tickers | 7+ at once (sweep) | 1 deep dive |
| Data type | OHLCV / technicals / signals | Primary filings / multiples / qualitative |
| Tools | yfinance, agentictendies, backtester | SEC EDGAR, NASDAQ API, StockAnalysis, news RSS |
| Output | Cron markdown + Discord msg | Saved note in /opt/data/notes/ + chat summary |
| Cadence | Every 15 min cron | On-demand |
| Time budget | 5-10 min | 15-30 min |

## Output format (user expects both)

1. **Saved file** at `/opt/data/notes/{TICKER}-{YYYY-MM-DD}.md` (~5-10 KB)
2. **Chat reply** with: 1-line verdict + key numbers + 5-bullet decision tree + 2-3 specific price levels

User pattern (verified): "看视频" → "你觉得这个有道理吗" → "有道理的话写小笔记" → "Dig into [TICKER]". The "写小笔记" verb is signal to save to disk.

---

## Workflow (15-30 minutes total)

### Step 1 — Get current market data (1-2 min)

**Primary — NASDAQ API (no auth, reliable):**
```bash
# Live price
curl -sL "https://api.nasdaq.com/api/quote/VRT/info?assetclass=stocks" -A "Mozilla/5.0"

# Summary stats
curl -sL "https://api.nasdaq.com/api/quote/VRT/summary?assetclass=stocks" -A "Mozilla/5.0"

# Quarterly income statement
curl -sL "https://api.nasdaq.com/api/company/VRT/financials?statement=IncomeStatement&period=quarterly&limit=8" -A "Mozilla/5.0"
```

**Fallback — Yahoo chart API for OHLCV (no auth):**
```bash
# 2-year daily history (~500 bars)
curl -sL "https://query1.finance.yahoo.com/v8/finance/chart/VRT?range=2y&interval=1d" -A "Mozilla/5.0"

# Quote stats (YH v7/v10 often blocked — try this fallback)
curl -sL "https://query1.finance.yahoo.com/v6/finance/quote?symbols=VRT" -A "Mozilla/5.0"
```

**Peer multiples — StockAnalysis.com (HTML scrape with regex):**
```bash
for sym in VRT GEV ETN NVT SCHN EMR; do
  curl -sL "https://stockanalysis.com/stocks/$sym/statistics/" -A "Mozilla/5.0" -o /tmp/sa_$sym.html
done
# Extract: PE Ratio, Forward PE, Beta, Revenue Growth (YoY)
python3 -c "
import re
for sym in ['VRT','GEV','ETN']:
    html=open(f'/tmp/sa_{sym}.html').read()
    text=re.sub(r'<[^>]+>',' ',html); text=re.sub(r'\\s+',' ',text)
    for kw in ['Forward PE','PE Ratio','Beta','Revenue Growth']:
        m=re.search(re.escape(kw)+r'\\s*([\\d\\.]+)',text)
        if m: print(f'{sym} {kw}: {m.group(1)}')
"
```

**⚠️ Pitfall — StockAnalysis blocks `requests` user-agents but accepts `Mozilla/5.0`**

### Step 2 — Find CIK and pull primary filings (3-5 min)

**Step 2a — Get CIK from company search:**
```bash
curl -sL "https://efts.sec.gov/LATEST/search-index?q=%22Vertiv%22&dateRange=custom&startdt=2026-04-22&enddt=2026-06-01&forms=8-K" \
  -A "Mozilla/5.0" | python3 -c "
import sys,json
d=json.load(sys.stdin)
for h in d['hits']['hits'][:5]:
    s=h['_source']
    print(s.get('ciks'),'|',s.get('file_date'),'|',h.get('_id'))
"
# Output: ['0001674101'] | 2026-04-22 | 0001628280-26-026379:vrt-20260422.htm
```

**Step 2b — Get the 8-K index page to find the press-release exhibit:**
```bash
CIK=1674101
ACC=000162828026026379
curl -sL "https://www.sec.gov/Archives/edgar/data/${CIK}/${ACC}/" -H "User-Agent: HermesResearch research@example.com" \
  | grep -oE 'href="[^"]*"' | grep -iE "exhibit|press|99"
# → q12026exhibit991vrt04222026.htm
```

**Step 2c — Fetch the press release / 10-Q / 10-K:**
```bash
curl -sL "https://www.sec.gov/Archives/edgar/data/1674101/000162828026026379/q12026exhibit991vrt04222026.htm" \
  -H "User-Agent: HermesResearch research@example.com" -o /tmp/vrt_q1.html
```

**⚠️ CRITICAL PITFALL — SEC EDGAR blocks default curl UAs:** Must use `-H "User-Agent: HermesResearch research@example.com"` (any realistic name + email). Without it, returns HTTP 403 with no body. This is the #1 time-sink on first attempt.

**Step 2d — Parse press release for key sections:**
```python
import re
html=open('/tmp/vrt_q1.html').read()
text=re.sub(r'<[^>]+>',' ',html)
text=re.sub(r'&nbsp;|&#160;',' ',text)
text=re.sub(r'&amp;','&',text)
text=re.sub(r'&#8220;|&#8221;','"',text)
text=re.sub(r'&#8217;',"'",text)
text=re.sub(r'&#8211;','-',text)
text=re.sub(r'&#8226;','*',text)
text=re.sub(r'&#59;',';',text)
text=re.sub(r'\s+',' ',text)
# Search for key markers
for kw in ['Net sales','guidance','Reaffirm','backlog','Liquidity','dividend']:
    for m in re.finditer(re.escape(kw),text,re.IGNORECASE):
        idx=m.start()
        print(f'=== {kw} ==='); print(text[max(0,idx-50):idx+500])
        break
```

### Step 3 — Pull news flow (1-2 min)

**Google News RSS — no auth, returns 15-20 fresh headlines per query:**
```bash
curl -sL "https://news.google.com/rss/search?q=Vertiv+VRT+stock&hl=en-US&gl=US&ceid=US:en" -A "Mozilla/5.0" \
  | python3 -c "
import sys,re
xml=sys.stdin.read()
for it in re.findall(r'<item>(.*?)</item>',xml,re.DOTALL)[:20]:
    t=re.search(r'<title>(.*?)</title>',it,re.DOTALL)
    p=re.search(r'<pubDate>(.*?)</pubDate>',it,re.DOTALL)
    print((p.group(1)[:25] if p else '???'),'|',t.group(1)[:120] if t else '???')
"
```

**Variants to run (in parallel):**
- `"[TICKER] +stock"` — general
- `"[TICKER] +Q1+earnings"` — earnings coverage
- `"[TICKER] +upgrade+OR+target+OR+analyst"` — sell-side actions
- `"[TICKER] +acquisition+OR+M&A"` — corporate actions
- `"[TICKER] +May+2026+OR+June+2026"` — recent (replace month names)

### Step 4 — Identify price-action context (1-2 min)

```python
import json, datetime
d = json.load(open('/tmp/vrt_chart.json'))
ts, c = d['chart']['result'][0]['timestamp'], d['chart']['result'][0]['indicators']['quote'][0]['close']
# Worst recent days
for i in range(1, len(ts)):
    pct = (c[i]-c[i-1])/c[i-1]*100
    dt = datetime.datetime.fromtimestamp(ts[i], datetime.timezone.utc).date()
    if dt >= datetime.date(2026,4,1) and abs(pct) > 4:
        print(f"{dt}  {c[i-1]:.2f} -> {c[i]:.2f}  {pct:+.2f}%")
```

Then **cross-reference with news** to determine: was the move sector-wide or stock-specific?
- Same-day price action of peers (GEV, ETN, NVT) determines if it's a sector event
- If VRT -8% on day when peers are flat → stock-specific catalyst; investigate news on that date
- If VRT -8% on day when peers are -4% → sector event; look at macro/Treasury yields/AI capex headlines

### Step 5 — Synthesize and write the note (5-10 min)

**Note structure (proven format, ~5-10 KB):**

```markdown
# [Ticker] ([Exchange]) — 深度调研

**Snapshot date**: [DATE] (盘中)
**实时价**: $[PRICE] ([+/-%], 开 $[OPEN])
**市值**: $[MCAP]B
**Beta (5Y)**: [BETA]
**1Y 区间**: $[LOW] – $[HIGH] (当前位置 [N]%, 距 52w 高 [+/-]%)

---

## 1. 关键估值倍数（vs. 同业）

[Peer comparison table — 5-7 columns × 5-7 rows]

## 2. 财务质量 ⭐⭐⭐⭐⭐

### FY 2026 TTM

[Margin trend table — Revenue / Gross / Op / FCF / EBITDA over 3-4 FYs]

### Q1 2026 (most recent)

[Key beats, organic growth, FCF, liquidity, leverage]

### Management guidance

[Q + FY guide with explicit +/- bands]

## 3. 技术面 / 资金面

[50d/200d MA, RSI, 52w perf, short interest, insider %, institutional %]

## 4. 催化剂 & 风险

### 🟢 Bull catalysts (short-term)

[Table: event / date / nature]

### 🔴 Bear risks

[Table: risk / severity / explanation]

## 5. 时间线（recent key events）

[Chronological list with dates — M&A, cap raises, ratings, conference presentations]

## 6. 我自己的判断

### 当前状态

[Star ratings on 5-6 dimensions]

### 加仓决策的 5 个 bullet

[1. Business quality assessment]
[2. Valuation assessment]
[3. Recent stock-specific event as warning]
[4. Hold vs. add recommendation with current-price justification]
[5. Add triggers with specific price levels]

### 关键价位

- 支撑: $X, $Y, $Z
- 阻力: $X, $Y, $Z

### 关键日历

[Q+1 earnings date, conferences, capex announcements]

## 7. 一句话总结

> [Verdict: business / valuation / action]
```

### Step 6 — Chat reply (terse)

Reply in chat with this exact structure (5-7 paragraphs max):
1. **Verdict line**: business rating vs valuation rating
2. **Snapshot**: live price, intraday change, market cap, 52w range position
3. **Today's catalyst** (if any): what drove the move
4. **Business is real (or not)**: 4-5 key numbers
5. **Valuation is expensive (or not)**: peer comparison table
6. **5-bullet decision**: hold / don't add at current / add at $X / add big at $Y
7. **File saved at**: /opt/data/notes/...

User pattern: read the verdict + the decision tree, skip the rest. **Lead with the conclusion, justify with numbers, end with action.**

---

## Pitfalls (verified — these WILL bite you)

1. **SEC EDGAR blocks default curl UA with HTTP 403 and empty body.** Always use `-H "User-Agent: <Name> <email>"`. Email matters — `research@example.com` is a known good pattern. The 403 happens silently, you'll spend 10 min debugging before noticing the empty response.

2. **StockAnalysis.com HTML structure changes.** The current pattern uses `<td class="bolded svelte-1dxpo91">[NUMBER]</td>` style with class names containing `svelte-1dxpo91`. Don't hardcode these — extract numbers with `re.findall(r'[\d,]+\.?\d*', text)`. If SA returns 404 or empty, fall back to NASDAQ API or SEC filings.

3. **NASDAQ API returns dollars in THOUSANDS for income statement.** Example: `"$10,229,900"` means $10.23 BILLION, not $10.23 million. Always verify the scale by checking if annual revenue makes sense for the company size.

4. **Yahoo Finance v7/v10 quote API requires crumb cookie.** v8 chart works without auth, v6 quote works without auth, v7/v10 don't. Use v6 + v8 only.

5. **5-10 day "stock-specific" crashes often have no obvious news.** When VRT -8% with no news, the answer is usually: (a) options expiry (monthly OpEx around 3rd Friday), (b) end-of-day position trim, (c) pre-event positioning before a known catalyst. Check the date against earnings/conference dates.

6. **Use `json.load` to parse SEC EDGAR responses, not HTML scrape** — the `/LATEST/search-index?q=...` endpoint returns proper JSON. The HTML view at `/cgi-bin/browse-edgar` is harder to parse.

7. **Time budget:** If the user just asked for a quick "is X a buy?", you have 5-10 min. If they explicitly said "dig into" or "research", spend 20-30 min. Don't over-research on quick questions; don't under-research on deep dives.

8. **Saved note path:** Always `/opt/data/notes/{TICKER}-{YYYY-MM-DD}.md`. The directory exists and is writable by hermes user. Do NOT use `/opt/hermes/notes/` — that's owned by root and will fail with permission denied.

9. **Chat reply in user's language.** User (stangg) communicates in Chinese. Reply in Chinese, use English for tickers, numbers, and proper nouns. Same as `portfolio-research` convention.

10. **`delegate_task` subagents timeout at 600s on this research pattern.** 2 subagents timed out at 600s in this session (called for stock research + earnings detail). They get stuck in slow API calls. Do this research directly with `terminal` + `python3` calls, not via subagent. Use `delegate_task` only for narrow subtasks with predictable time (e.g., "scrape 5 specific URLs and return 1-line summaries each").

11. **When the user names a product/codename that returns 0 hits, do not give up after the first lookup — try the obvious sibling/prefix variants.** Verified 2026-06-02: stangg typed "nvidia rtx spark" which has 0 hits in SEC EDGAR + Yahoo. The actual product is "DGX Spark". The recovery was:
    - `efts.sec.gov/LATEST/search-index?q="<user phrase>"` → 0 hits
    - Yahoo Finance `<user phrase>` ticker feed → empty
    - Replace one product prefix with a sibling ("RTX" → "DGX" or "HGX" or "NVAE" — NVIDIA's three AI prefixes). Re-run.
    - If a close variant hits, write the note under the **real** name and explicitly note the user's original phrasing + the correction.
    - If no variant hits at all, write a 1-page note explaining what was searched, what was found, and your best guess at the intended name. The user can then clarify without re-explaining the search you already did.

12. **Yahoo Finance RSS is the right tool to check if a product/codename exists as a stock ticker.** Verified pattern: `curl -sS "https://feeds.finance.yahoo.com/rss/2.0/headline?s=<SYMBOL>&region=US&lang=en-US"` → if `<item>` elements appear, it's a real ticker; if the feed is empty (just `<title>Yahoo! Finance:  News</title>` with no items), the symbol is not listed. Run this for the literal string first, then for the most likely 2-3 variants. SEC EDGAR full-text is the parallel check for the same string as a product mention in 8-K/10-K filings.

13. **Always include the user's original phrasing in the saved note + chat reply** when you correct a misspelled name. The user wants to know (a) what they said, (b) what you found, (c) why you mapped one to the other. This avoids the "but I asked about X, not Y" follow-up.

---

## Companion skills

- **`portfolio-research`** — for multi-ticker technical scans, signals, backtests
- **`youtube-content`** — for video content (different domain)
- **`portfolio-research-cron-quantdinger`** — for the 15-min cron job

When user asks "should I add to [TICKER]", this skill produces the qualitative case. The cron job's quant signal provides the technical timing. Together: this skill = fundamental conviction, cron = entry timing.

## References

- `references/sec-edgar-patterns.md` — full SEC EDGAR access patterns, CIK discovery, 8-K exhibit retrieval, search-index API; SEC UA pitfall
- `references/peer-comparison-template.md` — ready-to-use peer table extraction script; handles GE Vernova, Eaton, nVent, Schneider, Emerson + 5 more industrial/AI peers
- `references/note-template.md` — full markdown note template with placeholder copy
