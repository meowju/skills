# Migrate-First: purpose-finder Size-Crisis Resolution

*Reference file for hermes-agent-skill-authoring — real case from purpose-finder Run 1*

---

## The Problem

purpose-finder v4.45.0 is a 32-section, 28-reference skill at 99,996 / 100,000 chars (4-char headroom). The Research Strategy has 8-cycle rotation covering: Ikigai → Frankl → Career Capital → Decision Frameworks → Flow → Identity → Monetize → Failure. **All 8 topics already exist in the file.** A cron run detecting "all topics present" and reporting `[SILENT]` is correct but leaves the skill permanently stuck — no subsequent cycle can add deepening content without first restoring headroom.

## The Correct Response

When headroom < 5,000 AND all verticals are covered → **migrate-first**, not silent exit.

Migration targets (high-value, repeatable):
1. **Founder Mode** (681 chars) — thin placeholder section that just links out. Inline the reference content and replace the link with a 300–500 char summary, freeing ~200 chars.
2. **Quick Scripts** section (1,964 chars) — already has a reference file (`quick-scripts-purpose.md` at 7,386 chars). Condense to 500 chars + keep the reference link.
3. **Decision Frameworks** (7,046 chars) — largest section. Migrate the Jeff Bezos regret-minimization case study and the Burnett/Evans Designing Your Life content to `references/decision-frameworks-deep.md`, replace with 500-char summaries + links.

## Migration Execution (Atomic)

```python
import pathlib, re

skill_path = "/opt/data/skills/productivity/purpose-finder/SKILL.md"
content = pathlib.Path(skill_path).read_text()
original_size = len(content)

# Track all migrations in memory
migrations = [
    # (old_string, new_string, section_name)
    (founder_mode_block, founder_mode_summary, "Founder Mode"),
    (quick_scripts_block, quick_scripts_summary, "Quick Scripts"),
    (decision_frameworks_block, decision_frameworks_summary, "Decision Frameworks"),
]

total_saved = 0
for old, new, name in migrations:
    saved = len(old) - len(new)
    total_saved += saved
    content = content.replace(old, new, 1)

new_size = len(content)
print(f"Migrated {len(migrations)} sections, saved {total_saved:,} chars")
print(f"New size: {new_size:,} / 100,000 | Headroom: {100000-new_size:,}")

assert new_size <= 100_000, f"Still over: {new_size:,}"
pathlib.Path(skill_path).write_text(content)

# Verify all reference links still valid
all_links = re.findall(r'\[([^\]]+)\]\(([^()]+)\)', content)
linked = {url for text, url in all_links if url.startswith('references/')}
ref_dir = pathlib.Path(skill_path).parent / "references"
orphans = sorted(set(f.name for f in ref_dir.glob("*.md")) - {url.replace('references/', '') for url in linked})
assert not orphans, f"Orphaned refs: {orphans}"
```

## Reference Mining as Parallel Strategy

While migrating, mine existing reference files for the target vertical. purpose-finder has rich references:
- `failure-purpose.md` — failure as directional signal
- `identity-habits-purpose.md` — identity-based habit formation
- `monetizing-purpose.md` — audience-first approach to monetization
- `range-generalist.md` — Epstein's range framework

The next deepening cycle (after migration restores headroom) should pull specific data from these references rather than doing new web research.

## Version Bump

After migration, bump patch version (4.45.0 → 4.45.1) with note: "Migrate-first: condensed Founder Mode, Quick Scripts, Decision Frameworks to create headroom for Run 2 deepening cycles."