# Verified-Fake Investigation Template (2026-06-02 case)

Reference case: "First Human Trial of a Senolytic Pill Reportedly Reverses Biological Age and Restores Hair and Muscle"

Use this as a worked example of how to structure a fact-check investigation note. Copy the structure; replace the content.

## Investigation log

**Headline:** "First Human Trial of a Senolytic Pill Reportedly Reverses Biological Age and Restores Hair and Muscle"
**Likely source (assumed):** Lifespan.io (longevity news blog) — guessed from search snippets
**Verdict:** FAKE / AI-generated clickbait — no primary source exists

### Source 1: Quoted-phrase search

```bash
# Bing
curl -sL -A "Mozilla/5.0" --max-time 25 \
  "https://www.bing.com/search?q=%22First+Human+Trial+of+a+Senolytic+Pill%22"
# → 0 real results; only the search interface echoing back the query

# DDG HTML
curl -sL -A "Mozilla/5.0" --max-time 25 \
  "https://html.duckduckgo.com/html/?q=%22First+Human+Trial+of+a+Senolytic+Pill%22"
# → 0 real results; only the "duckduckgo.com - html.duckduckgo.com" wrapper
```

**Interpretation:** Title appears nowhere on the open web except as a search query echo. This is a 99% fakery signal.

### Source 2: Google News RSS

```bash
curl -sL -A "Mozilla/5.0" --max-time 25 \
  "https://news.google.com/rss/search?q=senolytic+pill+reverses+biological+age+hair+muscle&hl=en-US&gl=US&ceid=US:en"
# → Returned unrelated stories (BBC, grape seed extract, etc.) — none matching the headline
```

**Interpretation:** No press coverage. Fake.

### Source 3: ClinicalTrials.gov API

```bash
curl -sL -A "Mozilla/5.0" --max-time 25 \
  "https://clinicaltrials.gov/api/v2/studies?query.term=senolytic&fields=NCTId,BriefTitle,OverallStatus,Phase,Condition,WhyStopped&pageSize=30"
# → 29 senolytic trials; none with hair regrowth as endpoint; none with "reverses biological age" primary outcome
```

**Interpretation:** The actual senolytic trial landscape is mostly:
- **D+Q (dasatinib + quercetin)** — Mayo Clinic, intermittent dosing
- **Fisetin** — Mayo Clinic AFFIRM-LITE (NCT03675724), COVID-FIS, COVFIS-HOME
- **Targeted indications:** bone, frailty, IPF, Alzheimer's (SToMP-AD), COVID, MS
- **Endpoints:** CTx bone marker, frailty index, DKK1, inflammatory cytokines
- **No trial** has "hair regrowth" or "muscle restoration" as primary or secondary endpoint

### Source 4: arXiv

```bash
curl -sL -A "Mozilla/5.0" --max-time 25 \
  "http://export.arxiv.org/api/query?search_query=senolytic+biological+age+human+trial&max_results=10"
# → 0 matching papers
```

**Interpretation:** Not surprising for a health claim (arXiv is mostly physics/ML). Not a signal in either direction.

### Source 5: Direct domain check

```bash
curl -sL -A "Mozilla/5.0" --max-time 25 \
  "https://www.lifespan.io/news/first-human-trial-of-a-senolytic-pill-reportedly-reverses-biological-age-and-restores-hair-and-muscle/" \
  -o /dev/null -w "HTTP=%{http_code} SIZE=%{size_download}\n"
# → HTTP=404 SIZE=347962 (404 page, ~350KB)
```

**Interpretation:** The most likely source URL doesn't exist.

## What's actually true (the real "firsts" being conflated)

Three real things the headline is probably mash-mashing:

1. **Life Biosciences partial cellular reprogramming** — FDA cleared Jan 2026 for first human trial, but:
   - Indication is **NAION (non-arteritic anterior ischemic optic neuropathy)** — blindness, not anti-aging
   - It's a **gene therapy** (AAV vector), NOT a pill
   - URL: https://www.nad.com/news/fda-greenlights-life-biosciences-human-study-setting-up-pivotal-test-for-aging-theory-from-harvards-david-sinclair
   - URL: https://www.technologyreview.com/2026/01/27/1131796/the-first-human-test-of-a-rejuvenation-method-will-begin-shortly/

2. **Mayo Clinic senolytic pill trials** — Real, ongoing, but modest endpoints:
   - **NCT03675724 AFFIRM-LITE** (fisetin, frailty in elderly) — recruiting
   - **NCT04313634** (D+Q for skeletal health) — completed, **negative result** for CTx bone marker
   - **NCT04063124 SToMP-AD** (D+Q for Alzheimer's) — completed Phase 1/2
   - **2024 Nature Medicine:** Intermittent senolytic therapy in postmenopausal women did NOT reduce serum CTx vs placebo

3. **2019 TRIIM trial** (Fahy et al., Aging Cell) — the only published "reversed biological age" study in humans:
   - Used **recombinant human growth hormone + metformin + DHEA**, NOT a senolytic
   - n=9, 1 year
   - Result: ~1.5 years GrimAge reversal
   - NOT replicated at scale; pilot study only

## The "hair + muscle" tell

**No senolytic RCT** has ever had "hair regrowth" or "muscle restoration" as a primary or secondary endpoint. The combination is a classic AI-generated clickbait mashup of:
- Mouse data: Xu et al. 2018, dasatinib+quercetin restored hair in aged mice
- Mouse data: senolytics improved grip strength in progeroid mice
- These are extrapolated to humans without any trial evidence

**Key user-facing heuristic:** "X pill reverses aging" headlines almost always combine (a) one real molecule, (b) one real mouse study, and (c) zero human trials. The "reverses" verb is doing a lot of work.

## Template for /opt/data/notes/ output

```markdown
# "{HEADLINE}" — Verdict: [FAKE / MISLEADING / REAL]

**Verdict (1-line):** [One sentence with the bottom line]

## Key facts (from investigation, YYYY-MM-DD)
- Bing quoted-phrase search: N real matches
- DDG HTML search: N real matches
- Google News RSS: N real matches
- ClinicalTrials.gov: N related trials, none with this specific endpoint
- arXiv: N matching papers
- Suspected source URL: HTTP NNN (real / 404 / 403)

## What is actually true (5-bullet decision tree)
1. If the headline cites a specific NCT number → ...
2. If the headline mentions a specific biomarker → ...
3. If the headline names a population/endpoint → ...
4. If the headline says "first" → ...
5. If the headline has no PI, no journal, no NCT, no DOI → fake/AI

## Real "first" candidates (specific names + price levels if investing)
- Company A (public/private, ticker) — what they actually do
- Company B — what they actually do
- Company C — what they actually do
- Public ETF plays: TICKER1, TICKER2

## Likely origin (best guess)
[One paragraph on what the headline is most likely mash-mashing]
```
