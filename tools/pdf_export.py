from __future__ import annotations

from pathlib import Path
import re
from typing import List

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    ListFlowable,
    ListItem,
    PageBreak,
)


# -------------------------------------------------------------------
# Public entry point
# -------------------------------------------------------------------

def export_markdown_to_pdf(markdown_path: str | Path, pdf_path: str | Path) -> Path:
    """
    Convert a markdown file to a PDF using ReportLab.

    Supports:
      - headings (#, ##, ###)
      - paragraphs
      - bullet lists
      - markdown tables
      - horizontal rules
      - fenced code blocks (basic paragraph rendering)

    Args:
        markdown_path: Path to source markdown file
        pdf_path: Path to output PDF file

    Returns:
        Path to generated PDF
    """
    markdown_path = Path(markdown_path)
    pdf_path = Path(pdf_path)

    text = markdown_path.read_text(encoding="utf-8")
    story = _build_story_from_markdown(text)

    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=letter,
        rightMargin=0.6 * inch,
        leftMargin=0.6 * inch,
        topMargin=0.6 * inch,
        bottomMargin=0.6 * inch,
        title=markdown_path.stem,
    )

    doc.build(story)
    return pdf_path


# -------------------------------------------------------------------
# Markdown parsing
# -------------------------------------------------------------------

def _build_story_from_markdown(markdown_text: str):
    styles = _build_styles()
    story = []

    lines = markdown_text.splitlines()
    i = 0
    in_code_block = False
    code_buffer: List[str] = []

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # -----------------------------------------------------------
        # fenced code block
        # -----------------------------------------------------------
        if stripped.startswith("```"):
            if not in_code_block:
                in_code_block = True
                code_buffer = []
            else:
                in_code_block = False
                code_text = "\n".join(code_buffer)
                if code_text.strip():
                    story.append(Paragraph(_escape(code_text).replace("\n", "<br/>"), styles["Code"]))
                    story.append(Spacer(1, 0.14 * inch))
            i += 1
            continue

        if stripped.startswith("#### "):
            story.append(Paragraph(_format_inline_markdown(stripped[5:].strip()), styles["Heading4"]))
            story.append(Spacer(1, 0.10 * inch))
            i += 1
            continue

        if stripped.startswith("##### "):
            story.append(Paragraph(_format_inline_markdown(stripped[6:].strip()), styles["Heading5"]))
            story.append(Spacer(1, 0.08 * inch))
            i += 1
            continue

        if in_code_block:
            code_buffer.append(line)
            i += 1
            continue

        # blank line
        if not stripped:
            i += 1
            continue

        # page break marker if you want to use it manually in md
        if stripped == "[[PAGEBREAK]]":
            story.append(PageBreak())
            i += 1
            continue

        # horizontal rule
        if re.fullmatch(r"[-*_]{3,}", stripped):
            story.append(Spacer(1, 0.10 * inch))
            story.append(Paragraph("<font color='#888888'>________________________________________</font>", styles["Body"]))
            story.append(Spacer(1, 0.10 * inch))
            i += 1
            continue

        # -----------------------------------------------------------
        # markdown table
        # -----------------------------------------------------------
        if _is_table_start(lines, i):
            table_lines = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                table_lines.append(lines[i])
                i += 1

            tbl = _markdown_table_to_flowable(table_lines, styles)
            story.append(tbl)
            story.append(Spacer(1, 0.18 * inch))
            continue

        # -----------------------------------------------------------
        # headings
        # -----------------------------------------------------------
        if stripped.startswith("# "):
            story.append(Paragraph(_format_inline_markdown(stripped[2:].strip()), styles["Heading1"]))
            story.append(Spacer(1, 0.16 * inch))
            i += 1
            continue

        if stripped.startswith("## "):
            story.append(Paragraph(_format_inline_markdown(stripped[3:].strip()), styles["Heading2"]))
            story.append(Spacer(1, 0.14 * inch))
            i += 1
            continue

        if stripped.startswith("### "):
            story.append(Paragraph(_format_inline_markdown(stripped[4:].strip()), styles["Heading3"]))
            story.append(Spacer(1, 0.12 * inch))
            i += 1
            continue

        # -----------------------------------------------------------
        # bullet list
        # -----------------------------------------------------------
        if re.match(r"^[-*]\s+", stripped):
            bullet_lines = []
            while i < len(lines):
                s = lines[i].strip()
                if re.match(r"^[-*]\s+", s):
                    bullet_lines.append(re.sub(r"^[-*]\s+", "", s))
                    i += 1
                else:
                    break

            items = [
                ListItem(Paragraph(_format_inline_markdown(item), styles["Body"]), leftIndent=12)
                for item in bullet_lines
            ]
            story.append(ListFlowable(items, bulletType="bullet"))
            story.append(Spacer(1, 0.12 * inch))
            continue

        # -----------------------------------------------------------
        # paragraph block
        # -----------------------------------------------------------
        para_lines = [stripped]
        i += 1
        while i < len(lines):
            nxt = lines[i].strip()
            if (
                not nxt
                or nxt.startswith("#")
                or nxt.startswith("|")
                or nxt.startswith("```")
                or nxt == "[[PAGEBREAK]]"
                or re.fullmatch(r"[-*_]{3,}", nxt)
                or re.match(r"^[-*]\s+", nxt)
            ):
                break
            para_lines.append(nxt)
            i += 1

        paragraph_text = " ".join(para_lines)
        story.append(Paragraph(_format_inline_markdown(paragraph_text), styles["Body"]))
        story.append(Spacer(1, 0.12 * inch))

    return story


# -------------------------------------------------------------------
# Table handling
# -------------------------------------------------------------------

def _is_table_start(lines: List[str], idx: int) -> bool:
    """
    Detect markdown table:
      | col1 | col2 |
      |------|------|
      | a    | b    |
    """
    if idx + 1 >= len(lines):
        return False

    first = lines[idx].strip()
    second = lines[idx + 1].strip()

    if not first.startswith("|"):
        return False

    # alignment separator row
    if re.match(r"^\|\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?$", second):
        return True

    return False


def _markdown_table_to_flowable(table_lines: List[str], styles):
    """
    Convert markdown table lines into a ReportLab Table.
    """
    rows = [_split_markdown_row(line) for line in table_lines]

    if len(rows) < 2:
        # fallback
        return Paragraph(_escape("\n".join(table_lines)).replace("\n", "<br/>"), styles["Code"])

    header = rows[0]
    body_rows = rows[2:]  # skip separator row

    all_rows = [header] + body_rows

    # normalize column count
    max_cols = max(len(r) for r in all_rows)
    normalized = []
    for row in all_rows:
        padded = row + [""] * (max_cols - len(row))
        normalized.append(padded[:max_cols])

    # wrap cell text in Paragraph so ReportLab can wrap lines properly
    table_data = []
    for r, row in enumerate(normalized):
        rendered_row = []
        for cell in row:
            cell_text = _format_inline_markdown(cell.strip())
            style = styles["TableHeader"] if r == 0 else styles["TableCell"]
            rendered_row.append(Paragraph(cell_text, style))
        table_data.append(rendered_row)

    # page width ~= 7.3 inches after margins
    total_width = 7.3 * inch
    col_widths = _calculate_column_widths(normalized, total_width)

    table = Table(
        table_data,
        colWidths=col_widths,
        repeatRows=1,
        hAlign="LEFT",
    )

    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#D9E2F3")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#A6A6A6")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F7F7F7")]),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )

    return table


def _split_markdown_row(line: str) -> List[str]:
    """
    Split a markdown table row into cells.

    Example:
      | Name | Value |
    -> ["Name", "Value"]
    """
    s = line.strip()

    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|"):
        s = s[:-1]

    return [cell.strip() for cell in s.split("|")]


def _calculate_column_widths(rows: List[List[str]], total_width: float) -> List[float]:
    """
    Very simple proportional sizing based on content length,
    with min/max constraints so columns don't collapse.
    """
    if not rows:
        return [total_width]

    col_count = max(len(r) for r in rows)
    lengths = [0] * col_count

    for row in rows:
        for i in range(col_count):
            value = row[i] if i < len(row) else ""
            lengths[i] = max(lengths[i], min(len(value), 60))

    # avoid zero widths
    lengths = [max(n, 8) for n in lengths]
    total_len = sum(lengths)

    raw_widths = [(n / total_len) * total_width for n in lengths]

    min_width = 1.0 * inch
    max_width = 3.2 * inch

    adjusted = [max(min_width, min(w, max_width)) for w in raw_widths]

    # rebalance to exact total width
    current_total = sum(adjusted)
    if current_total == 0:
        return [total_width / col_count] * col_count

    scale = total_width / current_total
    adjusted = [w * scale for w in adjusted]

    return adjusted


# -------------------------------------------------------------------
# Styles
# -------------------------------------------------------------------

def _build_styles():
    base = getSampleStyleSheet()

    styles = {
        "Heading1": ParagraphStyle(
            "Heading1Custom",
            parent=base["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=18,
            leading=22,
            spaceAfter=8,
            textColor=colors.black,
        ),
        "Heading2": ParagraphStyle(
            "Heading2Custom",
            parent=base["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=14,
            leading=18,
            spaceAfter=6,
            textColor=colors.black,
        ),
        "Heading3": ParagraphStyle(
            "Heading3Custom",
            parent=base["Heading3"],
            fontName="Helvetica-Bold",
            fontSize=12,
            leading=15,
            spaceAfter=4,
            textColor=colors.black,
        ),
        "Heading4": ParagraphStyle(
            "Heading4Custom",
            parent=base["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=10.5,
            leading=13,
            spaceAfter=4,
            textColor=colors.black,
        ),
        "Heading5": ParagraphStyle(
            "Heading5Custom",
            parent=base["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=9.5,
            leading=12,
            spaceAfter=3,
            textColor=colors.black,
        ),
        "Body": ParagraphStyle(
            "BodyCustom",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=9.5,
            leading=12,
            alignment=TA_LEFT,
            spaceAfter=4,
        ),
        "Code": ParagraphStyle(
            "CodeCustom",
            parent=base["BodyText"],
            fontName="Courier",
            fontSize=8.5,
            leading=10,
            backColor=colors.HexColor("#F4F4F4"),
            borderPadding=6,
            leftIndent=6,
            rightIndent=6,
            spaceAfter=6,
        ),
        "TableHeader": ParagraphStyle(
            "TableHeader",
            parent=base["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=8.8,
            leading=10.5,
            alignment=TA_LEFT,
        ),
        "TableCell": ParagraphStyle(
            "TableCell",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=10,
            alignment=TA_LEFT,
        ),
    }

    return styles


# -------------------------------------------------------------------
# Utilities
# -------------------------------------------------------------------

def _format_inline_markdown(text: str) -> str:
    """
    Convert a small subset of markdown inline formatting
    into ReportLab Paragraph-compatible markup.
    """
    text = _escape(text)

    # bold: **text**
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)

    # italic: *text*
    text = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"<i>\1</i>", text)

    # inline code: `text`
    text = re.sub(r"`(.+?)`", r"<font name='Courier'>\1</font>", text)

    return text


def _escape(text: str) -> str:
    """
    Minimal XML/HTML escaping for Paragraph content.
    """
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )