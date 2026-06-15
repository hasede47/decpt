from pathlib import Path

from docx import Document
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    KeepTogether,
    ListFlowable,
    ListItem,
    PageBreak,
    PageTemplate,
    Paragraph,
    Preformatted,
    Spacer,
    Table,
    TableStyle,
)


DOCS = Path(__file__).resolve().parent
DOCX = DOCS / "DECEPTR_Guide_Complet_Installation_Configuration.docx"
PDF = DOCS / "DECEPTR_Guide_Complet_Installation_Configuration.pdf"


def iter_blocks(parent):
    from docx.document import Document as DocumentType
    from docx.oxml.table import CT_Tbl
    from docx.oxml.text.paragraph import CT_P
    from docx.table import Table as DocxTable
    from docx.text.paragraph import Paragraph as DocxParagraph

    parent_elm = parent.element.body if isinstance(parent, DocumentType) else parent._tc
    for child in parent_elm.iterchildren():
        if isinstance(child, CT_P):
            yield DocxParagraph(child, parent)
        elif isinstance(child, CT_Tbl):
            yield DocxTable(child, parent)


def esc(text):
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace("\n", "<br/>")
    )


styles = getSampleStyleSheet()
styles.add(
    ParagraphStyle(
        "CoverKicker",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=12,
        textColor=colors.HexColor("#2E74B5"),
        alignment=TA_CENTER,
        spaceAfter=10,
    )
)
styles.add(
    ParagraphStyle(
        "CoverTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=26,
        textColor=colors.HexColor("#0B2545"),
        alignment=TA_CENTER,
        leading=31,
        spaceAfter=12,
    )
)
styles.add(
    ParagraphStyle(
        "CoverSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=12,
        textColor=colors.HexColor("#5A626E"),
        alignment=TA_CENTER,
        leading=16,
        spaceAfter=18,
    )
)
styles.add(
    ParagraphStyle(
        "H1Manual",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=17,
        textColor=colors.HexColor("#0B2545"),
        leading=21,
        spaceBefore=8,
        spaceAfter=9,
        keepWithNext=True,
    )
)
styles.add(
    ParagraphStyle(
        "H2Manual",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=13,
        textColor=colors.HexColor("#2E74B5"),
        leading=16,
        spaceBefore=10,
        spaceAfter=6,
        keepWithNext=True,
    )
)
styles.add(
    ParagraphStyle(
        "H3Manual",
        parent=styles["Heading3"],
        fontName="Helvetica-Bold",
        fontSize=11.5,
        textColor=colors.HexColor("#1F4D78"),
        leading=14,
        spaceBefore=8,
        spaceAfter=5,
        keepWithNext=True,
    )
)
styles.add(
    ParagraphStyle(
        "BodyManual",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=9.4,
        leading=12.2,
        spaceAfter=5,
    )
)
styles.add(
    ParagraphStyle(
        "CodeManual",
        parent=styles["Code"],
        fontName="Courier",
        fontSize=7.2,
        leading=8.4,
        leftIndent=5,
        rightIndent=5,
        spaceBefore=3,
        spaceAfter=6,
        backColor=colors.HexColor("#F6F8FB"),
    )
)
styles.add(
    ParagraphStyle(
        "CellManual",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=7.5,
        leading=9.2,
    )
)
styles.add(
    ParagraphStyle(
        "CellHeadManual",
        parent=styles["BodyText"],
        fontName="Helvetica-Bold",
        fontSize=7.7,
        leading=9.4,
        textColor=colors.HexColor("#0B2545"),
    )
)
styles.add(
    ParagraphStyle(
        "FooterManual",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        textColor=colors.HexColor("#5A626E"),
    )
)


def table_flowable(table):
    data = []
    for r_idx, row in enumerate(table.rows):
        out_row = []
        for cell in row.cells:
            text = "\n".join(p.text.strip() for p in cell.paragraphs if p.text.strip())
            style = styles["CellHeadManual"] if r_idx == 0 else styles["CellManual"]
            out_row.append(Paragraph(esc(text), style))
        data.append(out_row)
    if not data:
        return Spacer(1, 1)
    col_count = len(data[0])
    usable = 180 * mm
    widths = [usable / col_count] * col_count
    tbl = Table(data, colWidths=widths, repeatRows=1, hAlign="LEFT")
    tbl.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#B9C5D3")),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E8EEF5")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )
    return tbl


def paragraph_flowable(p, previous_h1):
    text = p.text.strip()
    if not text:
        return []
    style = p.style.name if p.style else ""
    if style == "Heading 1":
        flows = []
        if previous_h1 or text == "Sommaire":
            flows.append(PageBreak())
        flows.append(Paragraph(esc(text), styles["H1Manual"]))
        return flows
    if style == "Heading 2":
        return [Paragraph(esc(text), styles["H2Manual"])]
    if style == "Heading 3":
        return [Paragraph(esc(text), styles["H3Manual"])]
    if style == "CodeBlock":
        return [Preformatted(text, styles["CodeManual"], maxLineLength=95)]
    if style.startswith("List Bullet") or style.startswith("List Number"):
        return [Paragraph("- " + esc(text), styles["BodyManual"])]
    if text == "PROJET CYBERDECEPTION":
        return [Spacer(1, 35 * mm), Paragraph(esc(text), styles["CoverKicker"])]
    if text == "DECEPTR v1 MVP":
        return [Paragraph(esc(text), styles["CoverTitle"])]
    if text.startswith("Guide complet"):
        return [Paragraph(esc(text), styles["CoverSubtitle"])]
    return [Paragraph(esc(text), styles["BodyManual"])]


def footer(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor("#D0D6DE"))
    canvas.line(15 * mm, 12 * mm, 195 * mm, 12 * mm)
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#5A626E"))
    canvas.drawString(15 * mm, 7.5 * mm, "DECEPTR v1 MVP - Guide complet")
    canvas.drawRightString(195 * mm, 7.5 * mm, f"Page {doc.page}")
    canvas.restoreState()


def main():
    docx = Document(DOCX)
    pdf = BaseDocTemplate(
        str(PDF),
        pagesize=A4,
        leftMargin=15 * mm,
        rightMargin=15 * mm,
        topMargin=15 * mm,
        bottomMargin=18 * mm,
        title="DECEPTR v1 MVP - Guide complet installation et configuration",
        author="DECEPTR Project",
    )
    frame = Frame(pdf.leftMargin, pdf.bottomMargin, pdf.width, pdf.height, id="normal")
    pdf.addPageTemplates([PageTemplate(id="main", frames=[frame], onPage=footer)])

    story = []
    seen_h1 = False
    for block in iter_blocks(docx):
        if block.__class__.__name__ == "Paragraph":
            flows = paragraph_flowable(block, seen_h1)
            if block.style and block.style.name == "Heading 1":
                seen_h1 = True
            story.extend(flows)
        else:
            story.append(table_flowable(block))
            story.append(Spacer(1, 6))

    pdf.build(story)
    print(PDF)


if __name__ == "__main__":
    main()
