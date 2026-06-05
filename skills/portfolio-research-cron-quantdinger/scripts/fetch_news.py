"""Fetch Yahoo Finance RSS headlines for watchlist + portfolio tickers and
macro keywords. Return deduped, time-sorted, ticker-tagged news items.

Why stdlib (not feedparser):
- feedparser not in the agentictendies venv; stdlib xml.etree is enough
  for the simple RSS 2.0 / Atom payloads Yahoo returns.
- We control parsing 100% — feedparser's lenient HTML/date handling has
  bitten us in the past with non-UTC date strings.

Why Yahoo RSS (not Google News / NewsAPI):
- Free, no API key, no per-request cap visible at 15-min cadence.
- Per-ticker feeds are clean and ticker-relevant.
- 1xx-2xx responses are <50 KB each; 10 tickers + 4 macro = 14 req/run,
  well within Yahoo's rate limits at 4 runs/hour.

Usage:
    from fetch_news import fetch_all_news
    items = fetch_all_news(tickers=[...], keywords=[...], max_age_hours=12)

Returned item schema:
    {
        "ticker": "NVDA" | "MACRO" | "GOLD" | ...,
        "title": str,
        "link": str,
        "source": "Yahoo Finance",
        "published": datetime (UTC, tz-aware) or None,
        "guid": str,             # used for dedup
        "summary": str,          # <description> body, truncated
    }
"""
from __future__ import annotations

import os
import re
import json
import time
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime

USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 HermesResearch/1.0"
TIMEOUT = 8  # seconds per request
MAX_RETRIES = 2
MAX_ITEMS_PER_FEED = 8  # Yahoo returns ~20; cap to keep report compact
SUMMARY_MAX = 180  # chars in <description>

# Macro keyword → free-text search query appended to Yahoo's RSS
# Keep this list small (4-5). Each extra keyword = 1 extra HTTP req per run.
MACRO_KEYWORDS = {
    "Fed": "Federal Reserve interest rates",
    "AI": "AI artificial intelligence chips",
    "Gold": "gold price central bank",
    "Taiwan": "Taiwan TSMC geopolitics",
    "Crypto": "crypto regulation bitcoin",
}

YAHOO_TICKER_FEED = "https://feeds.finance.yahoo.com/rss/2.0/headline?s={sym}&region=US&lang=en-US"
YAHOO_SEARCH_FEED = "https://feeds.finance.yahoo.com/rss/2.0/headline?s={q}&region=US&lang=en-US"

# Words to skip in titles (lowercase substring match) — clickbait / spam
TITLE_SKIP_PATTERNS = [
    r"\bpremium\b",
    r"\bsubscriber\b",
    r"\bsign in to read\b",
    r"\bvideo transcript\b",
]


def _http_get(url: str) -> bytes | None:
    """Fetch URL with UA + retry. Return raw bytes or None on failure."""
    for attempt in range(MAX_RETRIES):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/rss+xml, application/xml;q=0.9, */*;q=0.8"})
            with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code in (429, 503) and attempt < MAX_RETRIES - 1:
                time.sleep(2 ** attempt)
                continue
            return None
        except Exception:
            if attempt < MAX_RETRIES - 1:
                time.sleep(1)
                continue
            return None
    return None


def _parse_date(s: str | None) -> datetime | None:
    """RFC 822 / ISO 8601 → tz-aware UTC datetime. None on failure."""
    if not s:
        return None
    s = s.strip()
    try:
        # RFC 822 (Yahoo default): "Tue, 02 Jun 2026 13:06:59 +0000"
        dt = parsedate_to_datetime(s)
        if dt is None:
            return None
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        pass
    try:
        # ISO 8601 fallback
        dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return None


def _strip_html(s: str | None) -> str:
    if not s:
        return ""
    s = re.sub(r"<[^>]+>", "", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def _parse_rss(xml_bytes: bytes, tag: str) -> list[dict]:
    """Parse RSS 2.0 items from Yahoo feed. Each item: {title, link, description, pubDate, guid}."""
    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError:
        return []
    items = []
    for item in root.iter("item"):
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        desc = _strip_html(item.findtext("description"))
        pub = _parse_date(item.findtext("pubDate"))
        guid = (item.findtext("guid") or link or title).strip()
        if not title or not link:
            continue
        items.append({
            "title": title,
            "link": link,
            "summary": desc[:SUMMARY_MAX] + ("…" if len(desc) > SUMMARY_MAX else ""),
            "published": pub,
            "guid": guid,
        })
    return items


def _should_skip_title(title: str) -> bool:
    low = title.lower()
    return any(re.search(p, low) for p in TITLE_SKIP_PATTERNS)


def _filter_recent(items: list[dict], max_age_hours: int) -> list[dict]:
    cutoff = datetime.now(timezone.utc) - timedelta(hours=max_age_hours)
    out = []
    for it in items:
        if it["published"] is None:
            # If Yahoo didn't return a date, keep it (better than dropping)
            out.append(it)
        elif it["published"] >= cutoff:
            out.append(it)
    return out


def fetch_ticker_news(ticker: str, max_age_hours: int = 12) -> list[dict]:
    """Fetch latest headlines for one ticker. Return list of items tagged with ticker."""
    url = YAHOO_TICKER_FEED.format(sym=ticker)
    raw = _http_get(url)
    if raw is None:
        return []
    items = _parse_rss(raw, ticker)
    items = _filter_recent(items, max_age_hours)
    items = [it for it in items if not _should_skip_title(it["title"])]
    items = items[:MAX_ITEMS_PER_FEED]
    for it in items:
        it["ticker"] = ticker
        it["source"] = "Yahoo Finance"
    return items


def fetch_keyword_news(label: str, query: str, max_age_hours: int = 12) -> list[dict]:
    """Fetch headlines for a macro keyword. Tag with `label` (e.g. 'Fed', 'AI')."""
    # Yahoo RSS search: q=NVR+OR+NVDA&...; we just use a free-text query
    # but Yahoo's search feed works best with a single term, so URL-encode
    # the query and let it match in the title/description.
    import urllib.parse
    encoded = urllib.parse.quote(query)
    url = f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={encoded}&region=US&lang=en-US"
    raw = _http_get(url)
    if raw is None:
        return []
    items = _parse_rss(raw, label)
    items = _filter_recent(items, max_age_hours)
    items = [it for it in items if not _should_skip_title(it["title"])]
    items = items[:MAX_ITEMS_PER_FEED]
    for it in items:
        it["ticker"] = label
        it["source"] = "Yahoo Finance"
    return items


def fetch_all_news(tickers: list[str], max_age_hours: int = 12, include_macros: bool = True) -> list[dict]:
    """Fetch + dedup across all tickers. Order: newest first.

    Dedup is by (title lower) — same headline on different feeds (e.g. NVDA
    and AI both surface the same item) gets one entry tagged with the first
    ticker we saw it under.
    """
    seen_titles: set[str] = set()
    out: list[dict] = []

    feeds = list(tickers)
    if include_macros:
        feeds.extend(MACRO_KEYWORDS.keys())

    for sym in feeds:
        if sym in MACRO_KEYWORDS:
            items = fetch_keyword_news(sym, MACRO_KEYWORDS[sym], max_age_hours)
        else:
            items = fetch_ticker_news(sym, max_age_hours)
        for it in items:
            key = re.sub(r"\W+", "", it["title"].lower())[:120]
            if key in seen_titles:
                continue
            seen_titles.add(key)
            out.append(it)

    out.sort(key=lambda x: x["published"] or datetime.min.replace(tzinfo=timezone.utc), reverse=True)
    return out


# --- Self-test: run a single ticker and print, useful for debugging ---
if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("usage: fetch_news.py TICKER [...]")
        sys.exit(1)
    items = fetch_all_news(sys.argv[1:], max_age_hours=24, include_macros=False)
    print(json.dumps([{k: (v.isoformat() if isinstance(v, datetime) else v) for k, v in it.items()} for it in items], indent=2, ensure_ascii=False))
