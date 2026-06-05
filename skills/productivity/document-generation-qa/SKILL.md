---
name: document-generation-qa
description: "Generate professional documents (PDF, DOCX, HTML) with mandatory self-review before delivery. Covers Python reportlab/pdfkit, Node.js, markdown-to-HTML pipelines. Includes rendering preview, visual QC checklist, and delivery workflow."
version: 0.1.0
author: badlands-labs
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [document, PDF, report, quality-control, self-review, delivery]
    related_skills:
      - productivity/nano-pdf
---

# Document Generation QA

Generate a document → **self-review it** → send or deliver. Never send a deliverable without checking it first.

## Core Principle

> "Visually inspect it before sending. Don't send me sloppy [deliverables]." — User feedback pattern

Self-review is not optional. A rejected deliverable wastes more time than a 5-minute QC pass.

---

## Workflow

### Step 1 — Generate Document

```python
# reportlab example
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

c = canvas.Canvas("output.pdf", pagesize=letter)
# ... draw content ...
c.save()
```

```python
# pymupdf rendering (for QA pass) — capture page_count BEFORE loop
import pymupdf
doc = pymupdf.open("output.pdf")
pc = doc.page_count            # ← capture count first!
mat = pymupdf.Matrix(2.0, 2.0)  # 2x resolution for QC
for i in range(pc):             # ← use captured count
    pix = doc[i].get_pixmap(matrix=mat)
    pix.save(f"/tmp/doc_page_{i+1:02d}.png")
```

### Step 2 — Self-Review Checklist

After generating, run through ALL of these before sending:

**Text integrity:**
- [ ] Extract full text via `pymupdf` (`page.get_text()`) — check for truncation, overflow, garbled characters
- [ ] Scan for text near page edges (`x > 570` for letter-size) — overflow = layout bug
- [ ] Verify page numbers are sequential and match document structure
- [ ] Check that multi-page documents don't have page 1 = cover + content merged

**Font hierarchy:**
- [ ] Cover title: 28–40pt bold
- [ ] Section headers: 16–20pt bold  
- [ ] Body text: 11–12pt (NOT 9pt — too small for professional docs)
- [ ] Captions/footnotes: 8–9pt minimum

**Layout:**
- [ ] Cover page is standalone (no content body on same page as title)
- [ ] Content flows naturally across pages — no orphaned headings
- [ ] Tables fit within margins
- [ ] Bullet lists render correctly with proper indentation

**Visual (render to PNG first):**
```python
# Always render to PNG at 2x before delivery
doc = pymupdf.open("output.pdf")
for i in range(doc.page_count):
    pix = doc[i].get_pixmap(matrix=pymupdf.Matrix(2.0, 2.0))
    pix.save(f"/tmp/preview_p{i+1:02d}.png")
```

### Step 3 — Send Preview First

Send 2–4 page PNG renders to user via Discord DM. Wait for feedback on specific issues. Then send the final PDF.

```
Discord target: discord:stancsz
```

### Step 4 — Delivery

Only after user approves the preview:
- Send the final PDF file via Discord DM
- File path format: `MEDIA:/full/path/to/file.pdf`

---

## Tools Available

| Tool | Use |
|------|-----|
| `reportlab` | Python PDF generation (canvas + platypus) |
| `pymupdf` | Python PDF rendering/QA extraction |
| `markdown` + `weasyprint` | HTML → PDF pipeline |
| `pandoc` | Docx/MD/HTML conversion |
| LibreOffice `--headless --convert-to pdf` | Office → PDF |

## Common Layout Bugs

| Bug | Cause | Fix |
|-----|-------|-----|
| Text overflows right edge | Content width > page width | Reduce font size or wrap text |
| Cover + content on same page | Content placed after cover without page break | Explicit `canvas.showPage()` |
| Wrong page numbers in footer | Footer hardcoded to section number | Compute actual document page number |
| Skills/tools list truncated | Column width too narrow for long names | Wrap or use two columns |
| Tiny body text (9pt) | Chosen for "more content fits" | 11pt minimum; less content per page is fine |

## Reportlab Platypus Tips

```python
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet

# Font hierarchy
styles = getSampleStyleSheet()
styles['Title'].fontSize = 36
styles['Heading1'].fontSize = 20
styles['Normal'].fontSize = 11  # NOT 9!

# Page break before new section
story.append(PageBreak())

# Colored horizontal rule
from reportlab.platypus import Flowable
class ColoredLine(Flowable):
    def __init__(self, width, color, thickness=1):
        Flowable.__init__(self)
        self.width = width
        self.color = color
        self.height = thickness
    def draw(self):
        self.canv.setStrokeColor(self.color)
        self.canv.setLineWidth(self.height)
        self.canv.line(0, 0, self.width, 0)
```

## Canvas-Based PDF (preferred for complex layouts)

For multi-page PDFs with per-page chrome (headers/footers, colored section bars), use `reportlab.pdfgen.canvas.Canvas` directly rather than `SimpleDocTemplate`. This gives full control over when and how pages are drawn.

```python
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

W, H = letter  # 612 × 792 pts
ML = 48; MR = W - 48; CW = MR - ML  # margins
TOP = H - 52 - 16  # below header bar
BOT = 46           # above footer bar

c = canvas.Canvas('/tmp/output.pdf', pagesize=letter)

# Draw cover (page 1 — no chrome)
c.setFillColor(DARK_NAVY); c.rect(0, 0, W, H, fill=1, stroke=0)
# ... cover content ...
c.showPage()  # ← commit page, advance counter

# For content pages: draw chrome then content
def draw_hf(c, pn, total):
    # Header bar
    c.setFillColor(DARK_NAVY); c.rect(0, H-52, W, 52, fill=1, stroke=0)
    c.setFillColor(white); c.setFont('Helvetica-Bold', 9)
    c.drawString(ML, H-22, 'BADLANDS LABS')
    # Footer with correct page number
    c.setFillColor(LIGHT_GREY); c.rect(0, 0, W, 36, fill=1, stroke=0)
    c.setFont('Helvetica-Bold', 8)
    c.drawRightString(MR, 13, f'Page {pn} of {total}')

# Page 2+
draw_hf(c, 2, TOTAL)
# ... draw content using c.drawString(), wrap_text_c(), etc. ...
c.showPage()  # commit page, page counter auto-increments
# ... repeat for all content pages ...

c.save()
```

Key canvas methods:
- `c.showPage()` — commits current page and increments the page counter
- `c.rect(x, y, w, h, fill=1)` — filled rectangle (backgrounds, bars)
- `c.drawString(x, y, text)` — single line of text
- `c.drawCentredString(cx, y, text)` — centered text
- `c.drawRightString(x, y, text)` — right-aligned text
- `c.setFont('Helvetica-Bold', size)` — font before drawing
- `c.setFillColor(hex_color)` — color before drawing
- `c.setStrokeColor(color)` / `c.setLineWidth(w)` — for borders/lines

### Text wrapping utility

```python
def wrap_text_c(c, text, x, y, width, font, size, color, leading=None):
    """Word-wrap text. Returns new y."""
    if leading is None:
        leading = size * 1.35
    words = text.split()
    line = ''
    c.setFont(font, size)
    c.setFillColor(color)
    for word in words:
        test = (line + ' ' + word).strip()
        if c.stringWidth(test, font, size) <= width:
            line = test
        else:
            if line:
                c.drawString(x, y, line); y -= leading
            line = word
    if line:
        c.drawString(x, y, line); y -= leading
    return y
```

### Page number bug (critical — wrong numbers propagate)

Original PDF had footer `Page 4 of N` on actual page 10. Root cause: page numbers were hardcoded as section counters instead of tracking the actual canvas page count. 

Fix: **track page number explicitly**. Do NOT use section indices or chapter numbers as page numbers. The `showPage()` call advances the canvas page counter — read it with `c._pageCount` or pass an explicit counter `pn` that you increment after each `showPage()`.

### pymupdf document closed after iteration

When rendering pages in a loop and then reading `doc.page_count` after the loop (or accessing `doc` after `doc.close()`), you get `ValueError: document closed`. Fix: capture `doc.page_count` **before** the loop, or don't call `doc.close()` until after all operations.

```python
doc = pymupdf.open('/path/to/file.pdf')
pc = doc.page_count      # ← capture BEFORE loop
for i in range(pc):       # ← use captured count, not doc.page_count in loop
    pix = doc[i].get_pixmap(matrix=pymupdf.Matrix(1.5, 1.5))
    pix.save(f'/tmp/p{i+1:02d}.png')
# doc.close()  # only if you need to, and after all ops
```

### Installing reportlab in locked venv

If `pip` is not available in the venv (common in hermes-agent's `.venv` which uses `uv` for package management), install via:

```bash
/usr/local/bin/uv pip install reportlab --python /opt/hermes/.venv/bin/python3 -q
```

Then import works: `sys.path.insert(0, '/opt/hermes/.venv/lib/python3.13/site-packages'); import reportlab`

## Discord Delivery Pattern

```python
# Step 1: Send preview message
send_message(action='send', message='PDF preview — pages 1-4', target='discord:stancsz')

# Step 2: Send PNG renders
for i in range(min(4, page_count)):
    send_message(action='send', message=f'MEDIA:/tmp/preview_p{i+1:02d}.png', target='discord:stancsz')

# Step 3: After approval — send final PDF
send_message(action='send', message='Final PDF', target='discord:stancsz')
send_message(action='send', message='MEDIA:/full/path/to/final.pdf', target='discord:stancsz')
```
