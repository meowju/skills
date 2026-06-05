---
name: fact-check-health-news
description: "Fact-check a health, biotech, or longevity news headline the user forwards — verify the claim's primary source, distinguish real clinical trials from clickbait/AI-generated content, and produce a 1-line verdict + 5-bullet decision tree. Use when user says 'find out about this headline', 'is this real', 'help me verify', or pastes a sensational claim like 'X reverses aging' / 'miracle cure Y' / 'new drug Z first human trial'. Do NOT use for: peer-reviewed paper deep-dive (use arxiv / research-paper-writing), single-ticker DD (use stock-fundamental-due-diligence)."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [fact-check, health, longevity, biotech, misinformation, clickbait, clinical-trials, research]
    related_skills: [arxiv, blogwatcher, portfolio-research, stock-fundamental-due-diligence]
---

## When to use this skill

Use when the user pastes or quotes a **sensational health/biotech/longevity headline** and asks for verification, or when something on social media reads like a "first ever" / "reverses aging" / "pill that does X" claim. Triggers include:

- "find out about this [headline]"
- "is this real / true / legit"
- "verify this claim" / "fact check"
- User pastes a clickbait headline and asks for context
- "what do we know about [drug/company/molecule]"

**Do NOT use for:**

- Peer-reviewed paper deep-dive (use `arxiv` or `research-paper-writing` skills)
- Single-ticker due diligence (use `stock-fundamental-due-diligence`)
- Multi-ticker scans (use `portfolio-research`)
- General web search ("what is metformin")

## The 3-question verdict (always lead with this)

For any health/biotech claim, the answer is determined by three questions. Ask them in order:

1. **Is there a primary source?** (clinical trial registry, peer-reviewed paper, FDA filing, company press release)
2. **If yes, does the headline accurately represent the primary source?** (most "reverses aging" headlines massively overstate)
3. **If no primary source exists → the headline is fake or AI-generated.** Period.

**Fast verdict line format (mandatory first line of reply):**

> 🔴 **Verdict:** FAKE / MISLEADING / OVERSTATED / REAL / WAIT-FOR-PEER-REVIEW

Always start the reply with this. The user is here to know whether to act on the headline, not to read a research report.

---

## The 5-source verification chain

Run sources in order; the **first source that yields a primary hit** is usually the answer. If sources 1-2 return zero real matches, the headline is almost certainly fake — do not waste time on sources 3-5.

### Source 1 — Quoted-phrase search on a major search engine (2 min)

Use **Bing** (best for quote matching, no JS required) or **DDG HTML endpoint** (`html.duckduckgo.com/html/?q=...`):

```bash
# Bing — wrap the EXACT headline in quotes
curl -sL -A "Mozilla/5.0" --max-time 25 \
  "https://www.bing.com/search?q=%22First+Human+Trial+of+a+Senolytic+Pill%22" \
  -o /tmp/bing.html -w "HTTP=%{http_code} SIZE=%{size_download}\n"
```

**Pitfall — search-engine `result__a` / `b_algo` extraction is fragile.** Bing uses `<li class="b_algo">` (deprecated in 2024-2025; sometimes `<h2><a>` only). DDG uses `class="result__a"`. Always:

1. Strip `<script>`/`<style>` first
2. Try `re.findall(r'<h2[^>]*>.*?<a[^>]*>(.*?)</a>', html, re.S|re.I)` for titles
3. Try `re.findall(r'href="(https?://[^"]+)"', html)` for URLs
4. **If the only matches are the search engine echoing back the query → headline is fake**

**Google returns 302 redirects on most queries** when accessed via curl — use Bing or DDG as primary. DDG HTML endpoint at `html.duckduckgo.com` is the only DDG URL that returns useful results via curl (the regular `duckduckgo.com` is JS-only).

### Source 2 — Google News RSS (1 min)

```bash
curl -sL -A "Mozilla/5.0" --max-time 20 \
  "https://news.google.com/rss/search?q=senolytic+pill+biological+age&hl=en-US&gl=US&ceid=US:en" \
  -o /tmp/gnews.xml
```

Parse with `re.findall(r'<title>(.*?)</title>', xml)` and `<item>` blocks. **If zero results → headline is fake or too niche for mainstream press.**

### Source 3 — ClinicalTrials.gov API (2 min)

```bash
# Search for the drug/trial
curl -sL -A "Mozilla/5.0" --max-time 20 \
  "https://clinicaltrials.gov/api/v2/studies?query.term=senolytic&fields=NCTId,BriefTitle,OverallStatus,Phase,Condition,WhyStopped&pageSize=20" \
  -o /tmp/ct.json
```

Parse with `json.load`. Each study is `studies[i].protocolSection.{identificationModule,statusModule,designModule}`. **If no trial matches the headline's specific endpoint or population → headline is fake.**

**Useful fields to request:** `NCTId`, `BriefTitle`, `OverallStatus`, `Phase`, `Condition`, `WhyStopped`, `InterventionName`, `PrimaryOutcomeMeasure`.

### Source 4 — arXiv (1 min)

```bash
curl -sL -A "Mozilla/5.0" --max-time 20 \
  "http://export.arxiv.org/api/query?search_query=senolytic+biological+age+human+trial&max_results=10" \
  -o /tmp/arxiv.xml
```

Parse with `xml.etree.ElementTree` and namespace `{"a": "http://www.w3.org/2005/Atom"}`. Iterate `entry` elements → `title`, `summary`, `published`. **arXiv is mostly ML/AI physics — for health claims, expect 0 hits. If 0, that's not evidence of fakery; just means the claim is not yet in preprint.**

### Source 5 — Wayback Machine + PubMed (5-10 min, only if 1-4 yield something)

Use Wayback for removed/orphaned articles; use NCBI E-utilities for PubMed:
```bash
# PubMed
curl -sL "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term=senolytic+biological+age&retmode=json&retmax=10"
curl -sL "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&id=PMID1,PMID2&retmode=json"
```

If you reach source 5, the claim is real enough to dig into — switch to the `arxiv` skill for the actual paper.

---

## 5-bullet decision tree (mandatory structure)

Every fact-check reply MUST include a 5-bullet decision tree under the verdict. Each bullet answers a specific yes/no question about the claim:

1. **If the claim cites a specific NCT number / DOI / journal** → how to verify
2. **If the claim mentions a specific biological marker** → how to verify (e.g., "biological age" → check if it's GrimAge / Horvath clock / DunedinPACE / PhenoAge — each has different validation levels)
3. **If the claim names a population/endpoint** → what real studies exist for that
4. **If the claim says "first"** → which 2-3 things it could be confusing (e.g., "first human trial" usually means a Phase 1 safety trial, NOT a "reverses aging" outcome)
5. **If the claim has no named PI, no journal, no NCT, no DOI** → conclude fake/AI-generated, give the telltale linguistic patterns

---

## Linguistic tells of AI-generated / clickbait health headlines

Train yourself to spot these:

| Phrase | What it actually means |
|---|---|
| "X reverses aging" | Usually mouse data extrapolated, or biomarker shift without functional improvement |
| "First human trial" | Usually a Phase 1 safety study (n<30, no efficacy), not a "first reversal" |
| "Cures" or "eliminates" cancer/disease | Editorial overstatement; real papers use "reduces progression" or "improves survival" |
| "Doctor-approved" / "scientists say" | No specific source — generic appeal to authority |
| "Restore[s] hair and muscle" combined | **The dead giveaway** — this combination has never appeared in any senolytic/metformin/Rapamycin human RCT primary endpoint |
| "in just X days/weeks" | Medical research timelines don't work this way for chronic conditions |
| "one simple trick" / "doctors hate" | Pure content farm; ignore |
| "pill" + "reverses" + a multi-system claim | Real pharmacology doesn't work that way — single drugs have single mechanisms |

---

## Common conflation patterns (the "real first" each headline is probably mis-mashing)

When a headline screams "first human trial of [X]" and you can't find it, it's almost always one of these real stories being mashed together:

- **Life Biosciences partial cellular reprogramming** (Sinclair) — FDA cleared 2026-01, but for NAION blindness, NOT anti-aging, and it's a **gene therapy** not a pill
- **Mayo Clinic senolytic trials** (NCT03675724 AFFIRM-LITE, NCT04063124 SToMP-AD) — real ongoing trials, mostly fisetin or D+Q, no "reverses aging" result yet
- **2019 TRIIM trial** (Fahy et al., Aging Cell) — only published "biological age reversed" study, but used GH+metformin+DHEA, n=9, ~1.5 yr GrimAge reversal
- **Metformin TAME-like proposals** — never enrolled; in planning
- **NMN/NR NAD+ precursors** — animal data, no human longevity result
- **Rapamycin off-label use** — anecdotal longevity claims, no RCT

---

## Reply format (Chinese — user is `stangg`, communicates in 中文)

Use this exact structure:

```
🔴/🟢 **Verdict:** [FAKE / MISLEADING / OVERSTATED / REAL / WAIT-FOR-PEER-REVIEW]
(1-line reason)

## 我具体怎么查的 (transparent, reproducible)
- Bing/DDG 引号搜原标题 → N 个真实匹配
- Google News RSS → N 匹配
- ClinicalTrials.gov → N 注册相关
- arXiv → N 论文
(only list sources you actually ran)

## 真实情况 / What's actually true
1. [first related real study with link/NCT/PI]
2. [second related real study]
3. [third if exists]
(be specific — names, dates, journals)

## "Hair + muscle" / [telltale combo] 是死穴
- 解释为什么这个组合在医学上是不可能的 / 极不寻常的

## 给读者的一句话
> [One-sentence takeaway the user can act on]
```

Length: 5-7 paragraphs total. The verdict + decision tree are the load-bearing parts.

---

## Pitfalls

1. **Don't trust "5 sources" if 0 returned real results — that's a fakery signal, not a failure.** 0 real matches on Bing quoted-phrase + 0 on Google News + 0 on ClinicalTrials.gov = 99% probability of fabricated headline. Stop digging, write the verdict.

2. **Google search via curl returns 302 redirects** with a giant obfuscated base64 blob. Don't waste time parsing it — use Bing or DDG.

3. **DuckDuckGo `duckduckgo.com` (no `/html/`) is JS-only and returns nothing useful via curl.** Always use `https://html.duckduckgo.com/html/?q=...`.

4. **Bing's HTML structure changes frequently.** `<li class="b_algo">` is deprecated; current Bing uses `<h2><a href="...">title</a></h2>` patterns nested in `<li>` containers. Fall back to extracting all `href="https://..."` URLs and `<h2>` text if `b_algo` returns 0.

5. **ClinicalTrials.gov `/api/v2/studies` requires a User-Agent** or it may throttle. Use `Mozilla/5.0`. The `fields=` parameter caps what comes back — request only what you need for speed.

6. **arXiv API has no UA requirement** but be polite; limit `max_results` to 10-20 to avoid timeouts.

7. **Quote characters in URLs**: encode as `%22` not `"` in `curl` URLs. Spaces as `+`.

8. **The answer is usually "what real thing is this headline confusing"** — not "is the molecule real." Molecule X may exist and be in trials; the headline is still fake if the trial doesn't claim what the headline says. Separate *existence of drug* from *truth of headline*.

9. **Don't write a 5-paragraph essay on the underlying biology** — user wants to know if they should believe the headline, not earn a PhD. 5 bullets + verdict is the right depth.

10. **Always save the investigation to a note** at `/opt/data/notes/{topic}-{YYYY-MM-DD}.md` (verdict + key numbers + 5-bullet decision tree + 2-3 specific names/levels). The user pattern (verified) is to forward the headline, get a verdict, and expect the file to exist.

---

## Companion skills

- **`arxiv`** — for when the headline turns out to be real and you need the actual paper
- **`stock-fundamental-due-diligence`** — for when the headline names a publicly traded company
- **`portfolio-research`** — for longevity/investment landscape context (UBX, Life Bio, etc.)
- **`blogwatcher`** — for monitoring if the same fake headline resurfaces on other sites
