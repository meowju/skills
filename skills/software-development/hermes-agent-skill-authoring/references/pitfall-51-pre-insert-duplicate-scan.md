# Pitfall 51: Pre-Insert Duplicate Scan — Before Adding `→ Full content:` Links

## The Pattern

Before inserting a new `→ Full content:` reference link into a skill, scan the **entire file** (not just the target section) for the same URL path. The URL may already be linked in a different section — adding it creates a true duplicate even though the new context is legitimate. The duplicate is only detectable by counting URL occurrences across the full file, not by checking within a single section.

## Real Case (breakup-recovery Run 57)

**What happened:** Added `anger-first-cycle.md` link to the Social Anger subsection (`### Social Anger — When Your Anger Has Other Targets`). The insertion was contextually appropriate — the four-stage anger cycle is directly relevant to understanding social anger triggers. But the URL was already linked in the Signs Anger Is Completing subsection of the same section. This created two occurrences of `references/anger-first-cycle.md` in the anger section.

**Detection:** `Counter(url for _, url in links).most_common()` showed `('references/anger-first-cycle.md', 2)`.

**Fix required:** Remove the duplicate link from the Social Anger subsection, version bump again (4.86→4.87). The original version bump (4.85→4.86) was clean — the second bump was the cost of the duplicate.

## Why This Isn't Obvious

When inserting a link into a specific section, the natural thought is "is this link already in this section?" — checking the local section context. The duplicate link was NOT in the Social Anger subsection, so the local check passed. The URL was linked in a *different* subsection (Signs Anger Is Completing), which is a legitimate cross-subsection reference. The new link was not wrong — it was contextually appropriate for Social Anger. The problem only surfaces when scanning the full file for the URL, not when checking the target section in isolation.

## The Pre-Insert Check

```python
# Before inserting any new → Full content: link
ref_url = "references/anger-first-cycle.md"
count_before = content.count(ref_url)
# count_before == 0 → URL not in file, safe to insert
# count_before == 1 → URL in one section, check if new location is intentional
# count_before >= 2 → already duplicated, fix the duplication first
```

## Decision Rules

| count_before | Action |
|--------------|--------|
| 0 | Safe to insert |
| 1 | URL already in one section — check if cross-subsection reference is intentional |
| ≥ 2 | True duplicate exists — fix before inserting |

**Cross-subsection same-URL references are sometimes intentional.** `references/anger-neuroscience.md` appears in both the Signs subsection and the Neuroscience subsection of the anger section — both links serve their respective subsections' content. When `count_before == 1`, manually inspect both locations to determine if the new link adds genuine value or is redundant.

## The Cost

One `content.count()` call before the insertion. The alternative is a version-bump cycle + subsequent patch to remove the duplicate after the fact. In cyclical cron runs, the version-bump cost compounds — the session that introduces the duplicate bumps the version, the next session detects and removes it, and the version number advances without corresponding content progress.

## Version Bump Without Content Progress (Related Cost)

When a session patches the version line but the content change introduces a duplicate that the next session must fix, the version number advances but the skill doesn't progress — the next session spent its patch on cleanup instead of addition. This is a hidden tax on skills that cycle through many runs: each unintended duplicate consumes a version number without advancing the skill's content.

**Rule:** Always do the pre-insert scan. The cost is one `content.count()` call. The savings are one version-bump cycle in the next session.