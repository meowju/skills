# Near-Limit Cyclical Job: Migrate-First Pattern

## The Problem

When a recurring cron job (e.g., ai-money-maker, wealth-mindset) targets a file >95k chars with headroom <5k, the default approach of "just patch and add content" fails at the size gate. The session needs to first free headroom before adding content.

## The Pattern

**Step 1: Identify the condensation candidate.** Find the largest inline section that already has a `→ Full content:` reference link. The reference file already contains the depth — the inline section is redundant storage.

**Step 2: Condense to summary + link.** Replace the large inline section with a 1–2 paragraph summary that preserves the `→ Full content:` reference link. The reference link is the signal that this section has been migrated.

**Step 3: Add new content.** With headroom freed, apply the new section insertion.

**Step 4: Atomic write.** Compute both operations (condense + add) in memory, write once.

## Real Case: wealth-mindset v1.129 → v1.130

| Metric | Value |
|--------|-------|
| Starting size | 99,097 chars |
| Headroom | 903 chars |
| Target addition | ~4,900 chars |
| Deficit | ~4,000 chars |

**Condensation candidate:** Buffett inline section — 9,730 chars, already linked to:
- `buffett-frameworks.md` (12,283 chars)
- `buffett-concentration-tax.md` (5,238 chars)

**Condensation result:** 9,730 → 1,501 chars (−8,229 chars)

**Addition:** 4,897-char new section "The Mathematics of Exponential Wealth"

**Final:** 95,766 chars, headroom 4,234, version 1.130.0

## Key Rule

> **Condense the section that already has the reference library — don't recreate content that already exists in references/.**

The skill's own `references/` directory is a content asset. When headroom is tight, mine the reference library by condensing inline sections that reference it, rather than removing the reference link entirely.

## Decision Tree

```
File size > 95k AND headroom < 5k?
  → YES: Find largest inline section with → Full content: link
       → Condense inline to 1-2 paragraph summary + preserve link
       → Compute combined delta in memory
       → Write once
       → Verify headroom ≥ 2k after write
  → NO:  Add content normally
```

## Headroom Thresholds (WSL Caching Warning)

In WSL environments, measured headroom can be inflated by up to 2x due to filesystem caching. Use Python `pathlib.read_text()` in the same session as the write to get the authoritative size. Treat reported headroom as optimistic — if it shows 900 chars, assume true headroom is ~400-500 until Python confirms otherwise.