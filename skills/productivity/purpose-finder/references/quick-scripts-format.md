# Quick Scripts Format Guide — Purpose Finder

*Session-specific formatting knowledge for the Purpose Finder Quick Scripts section.*

---

## Script Entry Format (SKILL.md Inline)

Quick Scripts in SKILL.md use a specific markdown format:

```
**"Script prompt text goes here"):**
> Response text goes here.
```

- **Bold double-quotes** (`**"..."**`) wrap the user's situation/distortion/prompt
- **Closing paren + colon** after the closing quote: `**"prompt"**):`
- **Blockquote** (`>`) for the response text
- **Blank line** between entries

**Example:**
```
**"My purpose keeps failing because I run out of money"):**
> There are two different problems here. First: the financial architecture of your life needs to be sustainable separate from your purpose work — purpose doesn't fund itself in the first 1-2 years. Second: maybe your purpose is right but the *business model* around it is wrong. Those require different fixes. The question isn't "should I keep going" — it's "what's actually broken: the direction or the funding structure?"

**"I don't know what I want"):**
> Not knowing is not permanent. What have you tried? Start trying things — the answer comes from living, not thinking.
```

## Script Entry Format (references/quick-scripts-purpose.md)

The expanded reference file uses a simpler blockquote format:

```
**"Prompt text":**
> Response text.
```

- No closing paren
- No colon after the closing quote
- Colon only after the entire `**"prompt"**` block

**Real entries from the reference file:**
```
**"I don't know what I want":**
> Not knowing is not permanent. What have you tried? Start trying things — the answer comes from living, not thinking.
```

## Format Consistency Issue

The two formats are not identical. When adding new scripts:

1. **SKILL.md inline scripts** — use `**"prompt"**):` with closing paren before colon
2. **references/quick-scripts-purpose.md** — use `**"prompt"**:` without closing paren

Adding a script to both files requires matching each file's format, not copy-pasting the same text.

## Script Count (as of this reference)

- SKILL.md Quick Scripts section: 11 scripts
- references/quick-scripts-purpose.md: 29+ scripts (expanded library)

## Adding a New Script

1. Write the new entry in both files using the correct format for each
2. Verify SKILL.md uses `**"prompt"**):` and references/ uses `**"prompt"**:`  
3. Count SKILL.md scripts after adding — stay within section size limits (~2,000 chars per additional script)
4. Run the verification: `content.count('**"')` should equal `content.count('**"):')`

## Quick Script Quality Bar

Good scripts:
- Name the specific distortion (not just the topic)
- Give a short answer first, then reframe
- Leave space for the user to respond (no lecturing)

Bad scripts:
- Generic ("I feel lost about my career")
- Long explanations in the response
- Multiple paragraphs (save longer responses for reference file)