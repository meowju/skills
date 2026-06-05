#!/usr/bin/env python3
"""Audit orphan reference files in ai-money-maker SKILL.md.

Run this after any session that creates, links, or reorganizes reference files.
Finds .md files in references/ that have no corresponding link in SKILL.md.

Usage: python3 scripts/audit-orphan-refs.py [skill-path]
Default skill-path: /opt/data/skills/productivity/ai-money-maker/SKILL.md
"""
import sys
import re
import pathlib

def audit_orphans(skill_path: str) -> list[str]:
    skill_path = pathlib.Path(skill_path)
    ref_dir = skill_path.parent / "references"

    content = skill_path.read_text()

    # Universal pattern: matches ANY bracketed link regardless of label text
    # Handles: → Full content: [X](refs/), → 完整内容： [X](refs/), raw [X](refs/)
    all_links = re.findall(r'\[([^\]]+)\]\(([^()]+)\)', content)
    linked = {url for text, url in all_links if url.startswith('references/')}
    linked_bare = {url.replace('references/', '') for url in linked}

    existing = {f.name for f in ref_dir.glob("*.md")} if ref_dir.exists() else set()
    orphans = sorted(set(existing) - linked_bare)
    return orphans

if __name__ == "__main__":
    skill_path = sys.argv[1] if len(sys.argv) > 1 else "/opt/data/skills/productivity/ai-money-maker/SKILL.md"
    orphans = audit_orphans(skill_path)
    print(f"Orphan reference files: {len(orphans)}")
    for o in orphans:
        print(f"  {o}")
    if not orphans:
        print("  (none — all reference files are linked)")
