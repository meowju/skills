# PDF Rendering & Visual QA Workflow

Use this when generating PDFs (via reportlab, fpdf, weasyprint, etc.) that will be sent to the user.

## Required Workflow: Render Before Send

**Never send a PDF without first rendering and visually inspecting it.**

### Step 1 — Install PyMuPDF for preview

```bash
uv pip install pymupdf
```

Note: the import name differs from the pip package:
```python
import sys
sys.path.insert(0, '/opt/hermes/.venv/lib/python3.13/site-packages')
import pymupdf
# NOT: from pymupdf import fitz
```

### Step 2 — Render pages as PNG

```python
import pymupdf

doc = pymupdf.open('/path/to/output.pdf')
print(f'Pages: {doc.page_count}')
mat = pymupdf.Matrix(1.5, 1.5)  # ~108 DPI for preview
for i in range(min(4, doc.page_count)):  # first 4 pages
    pix = doc[i].get_pixmap(matrix=mat)
    pix.save(f'/tmp/pdf_page_{i+1}.png')
doc.close()
```

### Step 3 — Send PNG previews to Discord DM for review

```python
send_message(action='send', target='discord:stancsz', message='Pages 1-4 preview')
send_message(action='send', target='discord:stancsz', message='MEDIA:/tmp/pdf_page_1.png')
# ... repeat for pages 2-4
```

Wait for user feedback. If formatting issues are reported:
- Identify specific pages/sections that need fixes
- Patch the Python script and regenerate
- Re-render and re-preview until user approves

### Step 4 — Send final PDF

Only after user confirms the preview looks good:
```python
send_message(action='send', target='discord:stancsz', message='Final PDF attached')
send_message(action='send', target='discord:stancsz', message='MEDIA:/path/to/final.pdf')
```

## Key Lessons

1. **Visual QA is mandatory** — user rejected the first PDF because formatting was sloppy. Do not skip the preview step.
2. **Discord DM target for this user**: `discord:stancsz`
3. **PyMuPDF import quirk**: pip package is `pymupdf`, import is `import pymupdf` (NOT `from pymupdf import fitz`)
4. **PDF tools available**: reportlab (installed via uv), no weasyprint/ghostscript/LibreOffice available in this env
5. **ReportLab Canvas API** preferred over Platypus — Platypus doctemplate has recursion issues with complex layouts

## PDF Generation Tools in This Environment

| Tool | Status | Notes |
|------|--------|-------|
| reportlab | ✅ Installed via `uv pip install reportlab` | Use Canvas API, avoid Platypus for complex layouts |
| PyMuPDF | ✅ Installed via `uv pip install pymupdf` | For PNG preview rendering only |
| fpdf/fpdf2 | ❌ Not available | |
| weasyprint | ❌ Not available | |
| wkhtmltopdf | ❌ Not available | |
| ghostscript | ❌ Not available | |
| LibreOffice | ❌ Not available | |
