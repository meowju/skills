# Subsection-Boundary Tail Corruption — Pitfall 48

Real case: purpose-finder Run 2. The "Frankl × Ikigai" bridge paragraph and `→ Full content: [references/ptg.md](references/ptg.md)` link were positioned between a `###` subsection (Space Between) and the next `##` framework header. A session computed section boundaries using the model "subsection ends at the nearest `\n##`" — this made the bridge and ref link appear to be inside the Space Between subsection body. A condensation patch that replaced the entire subsection body (using `\n## Framework: The Purpose Discovery Process` as the end anchor) deleted both the bridge and the reference link entirely.

**Why this fails silently:** The bridge paragraph and ref link are visually between the `###` header and `\n## Framework` in file order, so they look like a subsection tail. But they render at file level — not nested inside the subsection. The boundary model that treats `\n##` as the subsection end misclassifies them. The file still looks structurally correct on read; only a targeted check for the bridge paragraph's presence reveals the loss.

**Correct model:** A `###` subsection ends at the NEXT `\n###` OR the nearest `\n##`, whichever comes first — BUT only content that is genuinely nested between the `###` header line and that boundary is part of the subsection. File-level paragraphs that happen to sit between the `###` and `\n##` are NOT subsection content; they belong to the parent `##` section. When replacing a subsection body, the replacement must explicitly include any such file-level paragraphs that should be preserved — they will not survive the replacement automatically.

**Detection:** Before replacing any subsection body that ends with a reference link line immediately followed by `\n## `, check whether the ref link is nested inside the subsection or at file level. Always verify post-replacement that key paragraphs and reference links are still present — not just that file size is within limit.

**Prevention:** When extracting a subsection to condense or replace, explicitly identify which content belongs to the subsection vs. which is a file-level element that happens to be positioned between the subsection and the next `##` header. Never let the `\n##` boundary auto-terminate the replacement — control the exact end position by including any bridge paragraphs in the replacement new_value.

**Post-replacement verification checklist (run after any subsection body replacement):**
```python
assert "TARGET_KEY_PARAGRAPH" in new_content, "Bridge paragraph lost"
assert "references/ptg.md" in new_content, "Reference link lost"
assert len(new_content) <= 100_000, "File over limit"
```

Related: patch-mismatch-pitfalls.md (pitfalls 50–51) covers Python-first decision tree for targeted insertions.