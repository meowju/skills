# Peer Comparison Template — Verified June 2026

## Script (drop-in, modify peer list)

```python
#!/usr/bin/env python3
"""Peer comparison extractor. Outputs markdown table."""
import re
import subprocess

PEERS = {
    'VRT':  'Vertiv Holdings',
    'GEV':  'GE Vernova',
    'ETN':  'Eaton',
    'NVT':  'nVent Electric',
    'SCHN': 'Schneider Electric',
    'EMR':  'Emerson Electric',
    'PH':   'Parker Hannifin',
    'ROP':  'Roper Technologies',
    'TT':   'Trane Technologies',
    'CARR': 'Carrier Global',
}

# 1) Fetch
for sym in PEERS:
    subprocess.run([
        'curl', '-sL',
        f'https://stockanalysis.com/stocks/{sym.lower()}/statistics/',
        '-A', 'Mozilla/5.0',
        '-o', f'/tmp/sa_{sym}.html'
    ], check=False)

# 2) Extract
def extract(html, keys):
    text = re.sub(r'<[^>]+>', ' ', html)
    text = re.sub(r'\s+', ' ', text)
    out = {}
    for k in keys:
        m = re.search(re.escape(k) + r'\s*([\d.,]+)', text)
        out[k] = m.group(1) if m else 'N/A'
    return out

FIELDS = [
    'Market Cap', 'PE Ratio', 'Forward PE', 'PS Ratio', 'Forward PS',
    'PB Ratio', 'EV/Sales', 'EV/EBITDA', 'P/FCF', 'PEG Ratio',
    'Beta (5Y)', 'Revenue Growth (YoY)', 'Gross Margin', 'Operating Margin',
    'Profit Margin', 'FCF Margin', 'ROE', 'ROA', '52-Week Price Change'
]

# 3) Print table
print(f"{'Ticker':6s} {'Name':22s} | " + " | ".join(f"{f:>8s}" for f in FIELDS))
for sym, name in PEERS.items():
    try:
        html = open(f'/tmp/sa_{sym}.html').read()
        vals = extract(html, FIELDS)
        print(f"{sym:6s} {name:22s} | " + " | ".join(f"{vals[f]:>8s}" for f in FIELDS))
    except FileNotFoundError:
        print(f"{sym:6s} {name:22s} | (no data)")
```

## Output (VRT + peers, June 2026)

```
Ticker Name                  | Market Cap | PE Ratio | Forward PE |  PS Ratio | Forward PS | ...
VRT    Vertiv Holdings       |   123.98B |    81.12 |     47.30  |    11.32  |     8.37   | ...
GEV    GE Vernova            |   254.75B |    28.33 |     52.36  |     N/A   |     N/A    | ...
ETN    Eaton                 |   155.13B |    39.19 |     28.46  |     N/A   |     N/A    | ...
NVT    nVent Electric        |    27.40B |    56.39 |     35.09  |     N/A   |     N/A    | ...
EMR    Emerson Electric      |    79.12B |    33.29 |     21.16  |     N/A   |     N/A    | ...
```

## Common peer sets

### AI / data center power & cooling
- **VRT** (Vertiv) — leader
- **GEV** (GE Vernova) — gas/steam turbines + grid
- **ETN** (Eaton) — power distribution
- **NVT** (nVent) — enclosures, liquid cooling
- **SCHN** (Schneider Electric) — full stack
- **EMR** (Emerson) — process control + power
- **BE** (Bloom Energy) — fuel cells (AI power)

### Industrial conglomerates with data center exposure
- **HON** (Honeywell) — split into 3 in 2025
- **ROP** (Roper) — software + industrial
- **PH** (Parker Hannifin) — motion/control
- **TT** (Trane) — cooling (residential heavy but DC growing)
- **CARR** (Carrier) — HVAC

### Semiconductor capex beneficiaries (when VRT is the lens)
- **NVDA** — GPU
- **AMD** — GPU
- **AVGO** — networking
- **MU** — HBM
- **AMAT** / **LRCX** — equipment

### China ADRs (when VRT is the lens)
- **BABA** — cloud capex
- **JD** — cloud capex

## Peer set selection rules

1. **Same primary end market** (data center power → VRT, GEV, ETN, NVT, SCHN)
2. **Same scale (within 5x revenue)** — comparing $10B VRT to $250M peer is apples-to-oranges
3. **Different geographies OK** — VRT (US-heavy) vs SCHN (EU-heavy) is fine if they compete in same product
4. **At least 3 peers** — fewer and you can't triangulate
5. **Same valuation regime** — growth stock peers should all be growth stocks (don't mix VRT 79x PE with mature 15x PE utility)

## Reading the table

| Pattern | Meaning |
|---------|---------|
| Target PE > peer avg + Target growth > peer avg | Premium justified |
| Target PE > peer avg + Target growth = peer avg | Overvalued |
| Target PE = peer avg + Target growth > peer avg | Undervalued or unknown catalyst |
| Target PE < peer avg + Target growth < peer avg | Cheap for a reason |
| Target FCF Margin >> peer avg | Best-in-class operations |
| Target Beta > 1.5x peers | Higher volatility; size position accordingly |
