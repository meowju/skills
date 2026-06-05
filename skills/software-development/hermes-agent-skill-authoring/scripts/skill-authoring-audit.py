#!/usr/bin/env python3
"""
Skill Authoring Audit Script
Validates a SKILL.md for structural integrity — orphan references, duplicate
section numbers, backtick-format links, and size limits.

Usage:
  python3 skill-authoring-audit.py <path-to-SKILL.md>

Examples:
  python3 skill-authoring-audit.py /opt/data/skills/productivity/ai-money-maker/SKILL.md
  python3 skill-authoring-audit.py skills/software-development/hermes-agent-skill-authoring/SKILL.md
"""

import sys
import re
import pathlib
from collections import Counter

def audit_skill(skill_path: str) -> dict:
    path = pathlib.Path(skill_path)
    if not path.exists():
        return {"error": f"File not found: {skill_path}"}

    content = path.read_text()
    skill_dir = path.parent

    results = {
        "file": str(path),
        "size_chars": len(content),
        "size_ok": len(content) <= 100_000,
        "size_limit": 100_000,
        "frontmatter_ok": False,
        "version": None,
        "description_len": 0,
        "description_ok": False,
        "sections": [],
        "section_count": 0,
        "duplicate_sections": [],
        "subsections": [],
        "duplicate_subsections": [],
        "embedded_subsections": [],
        "ref_link_types": {"full_content": 0, "related": 0, "backtick": 0},
        "linked_refs": set(),
        "backtick_refs": set(),
        "orphan_refs": [],
        "duplicate_ref_links": [],
        "boundary_corruption": [],
        "errors": [],
    }

    # --- Frontmatter validation ---
    if not content.startswith("---"):
        results["errors"].append("Missing leading ---")
        return results

    m = re.search(r'\n---\n', content[3:])
    if not m:
        results["errors"].append("Missing closing ---")
        return results

    end_pos = 3 + m.start() + m.end() - 3
    fm_text = content[3:end_pos-3]

    if 'name:' not in fm_text:
        results["errors"].append("Missing 'name:' in frontmatter")
    if 'description:' not in fm_text:
        results["errors"].append("Missing 'description:' in frontmatter")

    results["frontmatter_ok"] = 'name:' in fm_text and 'description:' in fm_text

    desc_match = re.search(r'description:\s*["\']?(.+?)["\']?\s*\n', fm_text)
    if desc_match:
        results["description_len"] = len(desc_match.group(1))
        results["description_ok"] = results["description_len"] <= 1024
    else:
        results["description_len"] = -1
        results["description_ok"] = False

    version_match = re.search(r'version:\s*(\S+)', content)
    if version_match:
        results["version"] = version_match.group(1)

    body = content[end_pos:].strip()
    if not body:
        results["errors"].append("Empty body after frontmatter")

    # --- Section header scan ---
    section_matches = list(re.finditer(r'\n## ([一二三四五六七八九十VI]+)、', content))
    results["sections"] = [m.group(1) for m in section_matches]
    results["section_count"] = len(section_matches)

    dup_sections = [(num, cnt) for num, cnt in Counter(results["sections"]).items() if cnt > 1]
    results["duplicate_sections"] = dup_sections

    # --- Subsection scan ---
    sub_matches = list(re.finditer(r'\n### ([一二三四五六七八九十VI]+)、', content))
    results["subsections"] = [m.group(1) for m in sub_matches]

    dup_subs = [(num, cnt) for num, cnt in Counter(results["subsections"]).items() if cnt > 1]
    results["duplicate_subsections"] = dup_subs

    # --- Embedded subsection detection ---
    sections_with_pos = [(m.start(), m.group(1)) for m in section_matches]
    subsections_with_pos = [(m.start(), m.group(1)) for m in sub_matches]

    for sub_pos, sub_num in subsections_with_pos:
        parent_section = None
        for i, (sec_pos, sec_num) in enumerate(sections_with_pos):
            next_sec_pos = sections_with_pos[i+1][0] if i+1 < len(sections_with_pos) else len(content)
            if sec_pos < sub_pos < next_sec_pos:
                parent_section = f"## {sec_num}"
                break
        if parent_section and parent_section != f"## {sub_num}":
            results["embedded_subsections"].append(
                f"### {sub_num}、 embedded inside {parent_section} (should be ## {sub_num}、)"
            )

    # --- Reference link scan ---
    full_links = re.findall(r'→ Full content:\s*\[([^\]]+)\]\(([^()]+)\)', content)
    related_links = re.findall(r'→ Related:\s*\[([^\]]+)\]\(([^()]+)\)', content)
    backtick_links = re.findall(r'`(references/[^`]+)`', content)

    results["ref_link_types"]["full_content"] = len(full_links)
    results["ref_link_types"]["related"] = len(related_links)
    results["ref_link_types"]["backtick"] = len(backtick_links)

    linked_refs = {p for _, p in full_links + related_links}
    backtick_refs = set(backtick_links)
    results["linked_refs"] = linked_refs
    results["backtick_refs"] = backtick_refs

    # --- Orphan reference detection ---
    # Must normalize both sides to bare filenames — comparing 'xxx.md' against
    # 'references/xxx.md' always produces false orphans (pitfall 27h). The fix:
    # extract basename from all_refs (full paths) and compare against existing_files
    # (bare filenames). Real case: purpose-finder had 22 refs, all linked, but the
    # buggy comparison reported all 22 as orphans.
    ref_dir = skill_dir / "references"
    if ref_dir.exists():
        existing_files = {f.name for f in ref_dir.glob("*.md")}
        all_refs = linked_refs | backtick_refs
        # Normalize: strip 'references/' prefix from full paths to get bare filenames
        all_ref_basenames = {p.replace('references/', '') for p in all_refs}
        results["orphan_refs"] = sorted(existing_files - all_ref_basenames)
    else:
        results["orphan_refs"] = []

    # --- Duplicate reference link detection ---
    all_link_texts = [text for text, _ in full_links] + [text for text, _ in related_links]
    dup_links = [(txt, cnt) for txt, cnt in Counter(all_link_texts).items() if cnt > 1]
    results["duplicate_ref_links"] = dup_links

    # --- Boundary corruption detection (## AND ### headers) ---
    # CORRECT method: Python string ops, NOT the fragile \s*\n## regex (pitfall 27i).
    # \s matches [ \t\f\r\v] but NOT \n — regex fails to distinguish correct vs corrupt.
    # Correct check: between the )-ending link line and the next header, if it doesn't
    # start with \n\n, it's corruption. between.strip() is WRONG — use startswith('\n\n') only.
    # Pitfall 42: also check → Full content: before ### subsection headers (not just ##).
    corrupted = []
    for m in re.finditer(r'→ Full content:[^\n]+\)', content):
        link_end = m.end()
        next_nl = content.find('\n', link_end)
        if next_nl == -1:
            continue
        # Check next ## top-level header
        next_header = content.find('\n## ', link_end)
        between = content[next_nl:next_header] if next_header != -1 else content[next_nl:]
        if next_header != -1 and not between.startswith('\n\n'):
            corrupted.append(f"→ Full content: link at pos {m.start()} followed by ## without blank line")
        # Check next ### subsection header (pitfall 42: also catches ###, not just ##)
        next_sub = content.find('\n### ', link_end)
        if next_sub != -1:
            between_sub = content[next_nl:next_sub]
            if not between_sub.startswith('\n\n'):
                corrupted.append(f"→ Full content: link at pos {m.start()} followed by ### without blank line")
    results["boundary_corruption"] = corrupted

    return results

def print_results(r: dict):
    print("=" * 60)
    print(f"Audit: {r['file']}")
    print("=" * 60)

    if "error" in r:
        print(f"ERROR: {r['error']}")
        return

    print(f"\n--- Basic Checks ---")
    print(f"  Size: {r['size_chars']:,} / {r['size_limit']:,} chars {'✓' if r['size_ok'] else '✗ EXCEEDS LIMIT'}")
    print(f"  Version: {r['version'] or 'NOT FOUND'}")
    print(f"  Frontmatter: {'✓' if r['frontmatter_ok'] else '✗'}")
    print(f"  Description: {r['description_len']} chars {'✓' if r['description_ok'] else '✗ (>1024)'}")
    print(f"  Body empty: {'✗' if r.get('body_empty') else '✓'}")

    print(f"\n--- Sections ({r['section_count']} total) ---")
    if r['duplicate_sections']:
        print(f"  ✗ DUPLICATE SECTION NUMBERS: {r['duplicate_sections']}")
    else:
        print(f"  ✓ No duplicate section numbers")

    if r['duplicate_subsections']:
        print(f"  ✗ DUPLICATE SUBSECTION NUMBERS: {r['duplicate_subsections']}")
    else:
        print(f"  ✓ No duplicate subsection numbers")

    if r['embedded_subsections']:
        print(f"  ✗ EMBEDDED SUBSECTIONS (should be top-level ##):")
        for e in r['embedded_subsections']:
            print(f"     - {e}")
    else:
        print(f"  ✓ No embedded subsections")

    print(f"\n--- Reference Links ---")
    print(f"  → Full content: {r['ref_link_types']['full_content']}")
    print(f"  → Related: {r['ref_link_types']['related']}")
    print(f"  Backtick `references/`: {r['ref_link_types']['backtick']}")

    if r['orphan_refs']:
        print(f"  ✗ ORPHAN REFERENCE FILES ({len(r['orphan_refs'])}):")
        for f in r['orphan_refs']:
            print(f"     - {f}")
    else:
        print(f"  ✓ No orphan reference files")

    if r['duplicate_ref_links']:
        print(f"  ✗ DUPLICATE REFERENCE LINKS:")
        for txt, cnt in r['duplicate_ref_links']:
            print(f"     - '{txt}' appears {cnt} times")
    else:
        print(f"  ✓ No duplicate reference link lines")

    if r['boundary_corruption']:
        print(f"  ✗ BOUNDARY CORRUPTION (→ Full content: not separated from ## or ###):")
        for b in r['boundary_corruption']:
            print(f"     - {b}")
    else:
        print(f"  ✓ No boundary corruption")

    if r['errors']:
        print(f"\n--- Errors ---")
        for e in r['errors']:
            print(f"  ✗ {e}")

    issues = (
        len(r['duplicate_sections']) +
        len(r['duplicate_subsections']) +
        len(r['embedded_subsections']) +
        len(r['orphan_refs']) +
        len(r['duplicate_ref_links']) +
        len(r['boundary_corruption']) +
        (0 if r['size_ok'] else 1) +
        (0 if r['description_ok'] else 1) +
        len(r['errors'])
    )
    print(f"\n{'='*60}")
    if issues == 0:
        print("RESULT: ✓ PASS — no issues found")
    else:
        print(f"RESULT: ✗ FAIL — {issues} issue(s) found")
    print("=" * 60)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: python3 {sys.argv[0]} <path-to-SKILL.md>")
        sys.exit(1)

    skill_path = sys.argv[1]
    results = audit_skill(skill_path)
    print_results(results)

    issues = (
        len(results.get('duplicate_sections', [])) +
        len(results.get('duplicate_subsections', [])) +
        len(results.get('embedded_subsections', [])) +
        len(results.get('orphan_refs', [])) +
        len(results.get('duplicate_ref_links', [])) +
        len(results.get('boundary_corruption', [])) +
        (0 if results.get('size_ok') else 1) +
        (0 if results.get('description_ok') else 1) +
        len(results.get('errors', []))
    )
    sys.exit(0 if issues == 0 else 1)