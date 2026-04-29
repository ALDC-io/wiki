#!/usr/bin/env python3
"""Convert navira-access-briefing.md to a styled HTML file for PDF export."""

import markdown
from pathlib import Path
import re

HERE = Path(__file__).resolve().parent
SRC = HERE / "navira-access-briefing.md"
OUT = HERE / "navira-access-briefing.html"

md_text = SRC.read_text(encoding="utf-8")

# Strip YAML frontmatter
md_text = re.sub(r"^---\n.*?---\n", "", md_text, count=1, flags=re.DOTALL)

html_body = markdown.markdown(
    md_text,
    extensions=["tables", "fenced_code", "md_in_html"],
)

html_doc = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Navira — API Access Briefing</title>
<style>
  @page {{
    margin: 1.5cm 2cm;
    size: A4;
  }}
  * {{
    margin: 0;
    padding: 0;
    box-sizing: border-box;
  }}
  body {{
    font-family: "Segoe UI", system-ui, -apple-system, sans-serif;
    font-size: 13px;
    line-height: 1.6;
    color: #1a2332;
    max-width: 850px;
    margin: 0 auto;
    padding: 40px 32px;
    background: #fff;
  }}
  h1 {{
    font-size: 1.7rem;
    font-weight: 600;
    color: #0f1923;
    margin-bottom: 8px;
    padding-bottom: 12px;
    border-bottom: 2px solid #2563eb;
  }}
  h2 {{
    font-size: 1.15rem;
    font-weight: 600;
    color: #0f1923;
    margin-top: 28px;
    margin-bottom: 10px;
    padding: 8px 14px;
    background: #f0f4ff;
    border-left: 4px solid #2563eb;
    border-radius: 0 6px 6px 0;
    page-break-after: avoid;
  }}
  h3 {{
    font-size: 1rem;
    font-weight: 600;
    color: #1e3a5f;
    margin-top: 20px;
    margin-bottom: 8px;
    page-break-after: avoid;
  }}
  p {{
    margin-bottom: 8px;
  }}
  strong {{
    color: #0f1923;
  }}
  hr {{
    border: none;
    border-top: 1px solid #e2e6ec;
    margin: 20px 0;
  }}
  table {{
    width: 100%;
    border-collapse: collapse;
    margin: 10px 0 16px;
    font-size: 12.5px;
  }}
  th {{
    background: #1e3a5f;
    color: #fff;
    font-weight: 600;
    text-align: left;
    padding: 8px 12px;
    font-size: 12px;
  }}
  td {{
    padding: 7px 12px;
    border-bottom: 1px solid #e8ecf0;
    vertical-align: top;
  }}
  tr:nth-child(even) td {{
    background: #f8f9fb;
  }}
  blockquote {{
    margin: 12px 0;
    padding: 10px 16px;
    background: #fffbeb;
    border-left: 4px solid #f59e0b;
    border-radius: 0 6px 6px 0;
    font-size: 12.5px;
    color: #78350f;
  }}
  blockquote strong {{
    color: #78350f;
  }}
  ol, ul {{
    margin: 6px 0 12px 24px;
  }}
  li {{
    margin-bottom: 4px;
  }}
  del {{
    color: #9ca3af;
    text-decoration: line-through;
  }}
  code {{
    background: #f1f5f9;
    padding: 1px 5px;
    border-radius: 3px;
    font-size: 12px;
    font-family: "Cascadia Code", "Fira Code", monospace;
    color: #2563eb;
  }}
  .header-meta {{
    font-size: 12.5px;
    color: #5a6a7e;
    margin-bottom: 16px;
  }}
  .header-meta strong {{
    color: #4a5a6e;
  }}
  @media print {{
    body {{
      padding: 0;
    }}
    h2 {{
      break-after: avoid;
    }}
    table {{
      break-inside: avoid;
    }}
    blockquote {{
      break-inside: avoid;
    }}
  }}
</style>
</head>
<body>
{html_body}
<div style="margin-top: 40px; padding-top: 16px; border-top: 1px solid #e2e6ec; font-size: 11px; color: #8a96a6; text-align: center;">
  Analytic Labs Data Corp — Navira Integration
</div>
</body>
</html>
"""

OUT.write_text(html_doc, encoding="utf-8")
print(f"Exported: {OUT}")
print(f"Open in browser and Ctrl+P to save as PDF.")
