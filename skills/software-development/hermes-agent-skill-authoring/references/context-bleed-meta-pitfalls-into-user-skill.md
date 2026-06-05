# Pitfall N: Context Bleed — Meta-Pitfalls from One Workflow Infecting a Different Skill

## Symptom

A user-facing skill (one that talks to humans about their problems) contains advice or pitfall entries that reference tool-internal concepts: `pathlib`, `skill_view`, `patch`, `headroom`, `100_000 chars`, `user-local tree`, `in-repo skill`, `git add`, `commit`, "headroom before patching," or any phrase that only makes sense in the skill-authoring / development workflow. The receiving skill is a *content* skill, not a *dev* skill.

## Real Case (Purpose-Finder Run 30 inspection)

`/opt/data/skills/productivity/purpose-finder/SKILL.md` Common Pitfalls section contained:

> 11. **"I'm in the right tree, patching the right file."** — `skill_view` on an in-repo skill returns a preview; `patch` edits the user-local tree. After patching, compare the `version:` field in both trees.
>
> 12. **"I need to check headroom before expanding."** — Always run the size gate before patching: `headroom = 100_000 - len(pathlib.Path(skill_path).read_text())`.

A person seeking life purpose is being told to run a Python size gate. This is the most diagnostic kind of corruption: the *content* of the entry makes sense (in another context) but the *recipient* is wrong. The user-facing skill's Common Pitfalls section is for *user obstacles* ("I'm too old to start," "What if I choose wrong," "I have no motivation") — not for *the agent's tooling obstacles*.

## How This Happens

Three typical paths, in order of frequency:

1. **Reference search hits a skill-authoring reference file.** A session that surveys existing skill pitfalls (e.g., "what's a good pitfall about size limits?") may pull from `hermes-agent-skill-authoring` references and paste them inline into a different skill without checking the *recipient domain*.

2. **Pitfall-number collision drives copy-paste.** When a user-facing skill's "Common Pitfalls" section already has 10 entries and the new draft needs more, the session may pull from the most-recently-edited skill's pitfalls — which is often a dev skill because dev skills are edited more often.

3. **Co-located editing compounds it.** A session that has *just* finished editing `hermes-agent-skill-authoring` (or any dev skill) and moves to a content skill carries the dev-skill's vocabulary in scratch memory. The pitfalls the session thinks of first are the ones it was just writing.

## Detection Scan (Run on Any User-Facing Skill)

```python
import re, pathlib

skill_path = "/opt/data/skills/<category>/<name>/SKILL.md"
content = pathlib.Path(skill_path).read_text()

# Heuristic: dev-skill vocabulary that should not appear in user-facing pitfalls
# Tune the patterns to your actual dev-skill terminology
DEV_TERMS = [
    r"\bpathlib\b", r"\bskill_view\b", r"\bin-repo skill\b", r"\buser-local tree\b",
    r"\bheadroom\b", r"\b100[,]?000\b", r"\bgit add\b", r"\bgit commit\b",
    r"\bwrite_file\b", r"\bexecute_code\b", r"\bhermes-agent-skill-authoring\b",
    r"\breferences/\w+\.md", r"\bSKILL\.md\b",  # link-style references in user content
    r"\bpatch\(.*\)", r"\bdelta\b",
]

# Scope: only the Common Pitfalls / Quick Scripts / When to Use sections
# are typically where user-facing content lives
sections_of_interest = re.split(r"\n## ", content)
for section in sections_of_interest:
    title_m = re.match(r"^([^\n]+)", section)
    if not title_m:
        continue
    title = title_m.group(1).strip()
    if not any(t in title for t in ["Pitfall", "Quick Script", "When to", "Conversation", "Common"]):
        continue
    for term in DEV_TERMS:
        for m in re.finditer(term, section):
            line_start = section.rfind("\n", 0, m.start()) + 1
            line_end = section.find("\n", m.end())
            if line_end == -1:
                line_end = len(section)
            line = section[line_start:line_end]
            ctx_section = title[:60]
            print(f"  [{ctx_section}] {term}: {line[:120]}")
```

If any line matches, the section has dev-skill bleed. Remove or rewrite the offending entry.

## Fix Pattern (Atomic, Single Section Replacement)

1. Identify the offending `N. **` entries in the Common Pitfalls section.
2. Replace them with entries the section's *recipient* would actually face (or remove them entirely if the user already has plenty).
3. **Renumber the remaining pitfalls** to close the gap (`13.` → `11.`, `14.` → `12.`).
4. Write once, atomic `pathlib.write_text()`.
5. Run the detection scan again — confirm zero hits.
6. Re-run orphan/reference-link checks if any `→ Full content:` link was removed.

## When Dev Pitfalls ARE the Right Content

A skill is dev-facing if it talks to an *agent operating on a tool surface*. Examples:
- `hermes-agent-skill-authoring` (this skill)
- Any skill whose Overview says "use when the agent needs to..."
- Any skill whose Quick Scripts reference Python `pathlib` patterns

For these, `pathlib`, `headroom`, `100_000` are appropriate. The detection scan should be restricted to *user-facing* skills — meaning skills that talk to humans about their problems.

**Quick test for "is this user-facing":** does the skill's Overview describe a person ("someone who feels X") or an agent ("an agent operating on Y")? If person → user-facing → run the bleed scan.

## Real Case Lessons (from Purpose-Finder Run 30)

- The corruption survived multiple prior runs because each run looked at *new* verticals to deepen, not at the existing pitfalls for hygiene. **Bleed-scan should be a Run-N≥5 step in any cyclical cron skill**, not just an inspection of the deepening target.
- The detection scan is fast (~10 lines of Python, runs in milliseconds). It should be a standard pre-edit survey on user-facing skills, like the orphan audit is for dev-facing skills.
- Cross-pollination is bidirectional: a content skill edited in the same session as a dev skill is at high risk. If a cron job alternates between content skills and dev skills in close temporal proximity, the bleed risk rises.
