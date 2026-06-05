# API Quirks for Health News Fact-Checking

Concrete gotchas from real verification runs. Update this file when you discover new failure modes.

## Bing search via curl

- **Endpoint:** `https://www.bing.com/search?q=%22exact+phrase%22`
- **User-Agent required:** `Mozilla/5.0` works; many others get redirected.
- **Result extraction — current state (Jun 2026):** The old `<li class="b_algo">` selector returns 0 results. Current Bing uses `<h2><a href="...">title</a></h2>` inside generic `<li>` containers. Reliable extraction:
  ```python
  import re
  html = open("/tmp/bing.html").read()
  # strip scripts/styles
  html = re.sub(r"<script[^>]*>.*?</script>", " ", html, flags=re.S|re.I)
  html = re.sub(r"<style[^>]*>.*?</style>", " ", html, flags=re.S|re.I)
  # titles
  titles = re.findall(r"<h2[^>]*>.*?<a[^>]*>(.*?)</a>", html, re.S|re.I)
  urls = re.findall(r'href="(https?://[^"]+)"', html)
  ```
- **"0 real results" signal:** If titles are empty AND URLs are mostly `bing.com/search?...` (query echo), the headline is fake. Don't bother parsing deeper.

## DuckDuckGo HTML endpoint

- **Correct URL:** `https://html.duckduckgo.com/html/?q=...` (the `/html/` path is required)
- **JS-only URL** (returns near-empty): `https://duckduckgo.com/?q=...`
- **Result class:** `class="result__a"` for titles, `class="result__snippet"` for snippets
- **Rate limit:** DDG will return 202/empty for repeated queries within seconds. Wait 5-10s between batches.

## Google search via curl

- **Returns 302 with obfuscated base64** — not parseable. Don't bother. Use Bing.

## Google News RSS

- **Endpoint:** `https://news.google.com/rss/search?q=QUERY&hl=en-US&gl=US&ceid=US:en`
- **No auth required.** Returns proper RSS XML.
- **Parse:** `re.findall(r'<item>(.*?)</item>', xml, re.S|re.I)` then extract `<title>`, `<pubDate>`, `<link>` from each item.
- **0 results for a specific claim** is a strong fakery signal.

## ClinicalTrials.gov API v2

- **Endpoint:** `https://clinicaltrials.gov/api/v2/studies?query.term=KEYWORD&fields=NCTId,BriefTitle,...&pageSize=20`
- **Format:** `format=json` (default) or omit. XML also available.
- **User-Agent:** `Mozilla/5.0` works; some UAs get throttled.
- **Key fields to request:** `NCTId`, `BriefTitle`, `OverallStatus`, `Phase`, `Condition`, `WhyStopped`, `InterventionName`, `PrimaryOutcomeMeasure`
- **WhyStopped** is gold — tells you if a trial died from futility, funding, or safety
- **Pagination:** use `pageToken` from response for >20 results
- **Result structure:** `studies[i].protocolSection.{identificationModule.nctId, statusModule.overallStatus, designModule.phases}`

## arXiv API

- **Endpoint:** `http://export.arxiv.org/api/query?search_query=...&max_results=10`
- **No auth, no UA requirement.**
- **Returns Atom XML**, not JSON.
- **Parse:**
  ```python
  import xml.etree.ElementTree as ET
  tree = ET.parse("/tmp/arxiv.xml")
  ns = {"a": "http://www.w3.org/2005/Atom"}
  for entry in tree.getroot().findall("a:entry", ns):
      title = entry.find("a:title", ns).text.strip()
      pub = entry.find("a:published", ns).text[:10]
  ```
- **Note:** arXiv is mostly physics/ML/AI. Health claim = expect 0 hits. Don't read into 0 results.

## PubMed E-utilities

- **esearch:** `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term=QUERY&retmode=json&retmax=10`
- **esummary:** `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&id=PMID1,PMID2&retmode=json`
- **No auth, but rate-limited** — 3 req/s without API key. With NCBI API key, 10 req/s.
- **Use this for real-paper confirmation, not for headline verification** — too slow for the first pass.

## Wayback Machine API

- **Availability check:** `https://archive.org/wayback/available?url=ENCODED_URL&timestamp=YYYYMMDD`
- **Use when:** a "real" article URL returns 404 — check if it ever existed and what it said.
- **No auth, no UA requirement.**

## Shell escaping when calling curl from execute_code

**⚠️ Common bug — f-string and curl format placeholders:**
```python
# WRONG — f-string tries to format %{http_code} as Python format spec
cmd = f"curl ... -w 'HTTP=%{{http_code}}'"  # ← OK actually, % is escaped
# But this FAILS:
cmd = f"curl -w 'HTTP=%{http_code}'"  # ← NameError: http_code not defined
```

**Fix:** Use `shlex.quote()` to avoid manual escaping, or use `%`-formatting instead of f-strings:
```python
import shlex
cmd = "curl -sL -A 'Mozilla/5.0' -w 'HTTP=%{http_code} SIZE=%{size_download}' " + shlex.quote(url)
```

Or build the string with `+` concatenation, never inside an `f"..."` if it contains `%{...}`.

## HTTP status / size pattern

Always log `HTTP=%{http_code} SIZE=%{size_download}` from curl. A 200 with SIZE=2000+ is real content; 200 with SIZE=300-1500 is usually an error/redirect page masquerading as 200; 404 is unambiguous.

## Common false-positive patterns

- **A 200 OK with title text but no <article> body** = the page rendered an error or 404 template. Always check for actual article content (paragraphs >40 chars), not just HTTP 200.
- **Cloudflare 403 with code 1010** = you're being blocked; switch source or add UA.
- **"We could not find..." text in the body** = even though the URL is the real domain, the specific path 404'd. Try the home page or `site:domain.com` search.
