from html import escape
from pathlib import Path

from docx import Document


DOCS = Path(__file__).resolve().parent
DOCX = DOCS / "DECEPTR_Guide_Complet_Installation_Configuration.docx"
HTML = DOCS / "DECEPTR_Guide_Complet_Installation_Configuration.html"


def iter_blocks(parent):
    from docx.document import Document as DocumentType
    from docx.oxml.table import CT_Tbl
    from docx.oxml.text.paragraph import CT_P
    from docx.table import Table
    from docx.text.paragraph import Paragraph

    if isinstance(parent, DocumentType):
        parent_elm = parent.element.body
    else:
        parent_elm = parent._tc

    for child in parent_elm.iterchildren():
        if isinstance(child, CT_P):
            yield Paragraph(child, parent)
        elif isinstance(child, CT_Tbl):
            yield Table(child, parent)


def paragraph_html(p):
    text = p.text.strip()
    if not text:
        return ""
    style = p.style.name if p.style else ""
    content = escape(text)
    if style == "Heading 1":
        return f"<h1>{content}</h1>"
    if style == "Heading 2":
        return f"<h2>{content}</h2>"
    if style == "Heading 3":
        return f"<h3>{content}</h3>"
    if style == "CodeBlock":
        return f"<pre><code>{content}</code></pre>"
    if style.startswith("List Bullet"):
        return f"<ul><li>{content}</li></ul>"
    if style.startswith("List Number"):
        return f"<ol><li>{content}</li></ol>"
    if style == "SmallNote":
        return f"<p class='small'>{content}</p>"
    return f"<p>{content}</p>"


def table_html(table):
    rows = []
    for r_idx, row in enumerate(table.rows):
        cells = []
        tag = "th" if r_idx == 0 else "td"
        for cell in row.cells:
            parts = []
            for p in cell.paragraphs:
                t = p.text.strip()
                if t:
                    parts.append(escape(t))
            cells.append(f"<{tag}>{'<br>'.join(parts)}</{tag}>")
        rows.append(f"<tr>{''.join(cells)}</tr>")
    return f"<table>{''.join(rows)}</table>"


def merge_lists(html):
    html = html.replace("</ul>\n<ul>", "\n")
    html = html.replace("</ol>\n<ol>", "\n")
    return html


def main():
    doc = Document(DOCX)
    body = []
    for block in iter_blocks(doc):
        if block.__class__.__name__ == "Paragraph":
            h = paragraph_html(block)
        else:
            h = table_html(block)
        if h:
            body.append(h)

    content = merge_lists("\n".join(body))
    html = f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>DECEPTR Guide Complet</title>
  <style>
    @page {{ size: A4; margin: 14mm; }}
    body {{
      font-family: "Segoe UI", Calibri, Arial, sans-serif;
      color: #142033;
      font-size: 10.5px;
      line-height: 1.42;
    }}
    h1 {{
      color: #0b2545;
      font-size: 20px;
      margin: 22px 0 10px;
      padding-bottom: 5px;
      border-bottom: 2px solid #2e74b5;
      break-after: avoid;
    }}
    h1:not(:first-child) {{ break-before: page; }}
    h2 {{
      color: #2e74b5;
      font-size: 15px;
      margin: 15px 0 7px;
      break-after: avoid;
    }}
    h3 {{
      color: #1f4d78;
      font-size: 13px;
      margin: 12px 0 6px;
      break-after: avoid;
    }}
    p {{ margin: 0 0 7px; }}
    .small {{ color: #5a626e; font-size: 9px; }}
    table {{
      width: 100%;
      border-collapse: collapse;
      margin: 8px 0 13px;
      page-break-inside: avoid;
    }}
    th {{
      background: #e8eef5;
      color: #0b2545;
      font-weight: 700;
    }}
    th, td {{
      border: 1px solid #b9c5d3;
      padding: 5px 6px;
      vertical-align: top;
      word-break: normal;
      overflow-wrap: anywhere;
    }}
    pre {{
      background: #f6f8fb;
      border-left: 4px solid #2e74b5;
      padding: 7px 9px;
      margin: 6px 0 10px;
      page-break-inside: avoid;
      white-space: pre-wrap;
      overflow-wrap: anywhere;
      font-size: 8.5px;
      line-height: 1.25;
    }}
    code {{
      font-family: Consolas, "Courier New", monospace;
    }}
    ul, ol {{ margin: 0 0 9px 22px; padding: 0; }}
    li {{ margin: 0 0 4px; }}
  </style>
</head>
<body>
{content}
</body>
</html>"""
    HTML.write_text(html, encoding="utf-8")
    print(HTML)


if __name__ == "__main__":
    main()
