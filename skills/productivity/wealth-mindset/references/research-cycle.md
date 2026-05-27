# Wealth-Mindset Research Cycle

This skill grows through a recurring 8-run research cycle. Each run picks ONE section to deeply improve, cycling through the major wealth-builder methodologies.

## The Cycle (repeat)

| Run | Focus | Section |
|-----|-------|---------|
| 1 | Elon Musk | Musk-Style Wealth Building |
| 2 | Jeff Bezos / Long-Term Thinking | Bezos-Style Wealth Building |
| 3 | Naval Ravikant | Naval Ravikant: How to Get Rich Without Getting Lucky |
| 4 | Warren Buffett | Buffett-Style Wealth Building |
| 5 | Power and Unstoppable Execution | Power and Unstoppable Execution |
| 6 | Income Acceleration | Income Acceleration sections |
| 7 | Risk and Probability Thinking | Risk and Probability Thinking |
| 8 | Tax Optimization | Tax Optimization and Asset Protection |

Then repeat, deepening each section with new research, data, and frameworks.

## Research Commands

Wikipedia API (factual content):
```bash
curl -sA "Mozilla/5.0" "https://en.wikipedia.org/w/api.php?action=query&titles=TOPIC&prop=extracts&explaintext=1&format=json&redirects=1"
```

## Growth Rules

- Keep existing content — add new sections, don't overwrite unless improving
- Update version number each run (patch level: X.Y.0 → X.Y+1.0)
- SKILL.md ceiling: 100,000 chars; migrate content to `references/` if needed
- Preserve: Overview, When to Use, Common Pitfalls, Quick Scripts, Verification Checklist
- Headroom target: keep at least 3,000 chars free for next expansion
- If headroom < 1,500 chars before a run: mine existing `references/` files first, then add synthesis

## Pre-Run Checklist

1. Read current SKILL.md size (`len(pathlib.read_text())`)
2. Check which section corresponds to this run's number (run mod 8, map to table above)
3. Read existing section to determine if it's a deepen (already exists) or expand (thin)
4. Research via Wikipedia API before writing
5. Apply expansion; bump version
6. Verify: size ≤ 100,000, no duplicate section headers, orphan refs = 0

## What Each Run Produces

- 3–5 bullet points of specific new content (tactical, not generic)
- One version bump
- One section updated or added
- Research discoveries noted for the delivery summary
