"""Render the complaint draft to PDF (reportlab, no external fonts or assets)."""

from __future__ import annotations

import io
import re
from typing import Any
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    ListFlowable,
    ListItem,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.actions.complaint import DRAFT_BANNER, ComplaintData, build_markdown


def _inline(s: str) -> str:
    s = escape(s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
    s = re.sub(r"_(.+?)_", r"<i>\1</i>", s)
    return re.sub(r"`(.+?)`", r"<font face='Courier'>\1</font>", s)


def render_pdf(d: ComplaintData, redact: bool = True) -> bytes:
    md = build_markdown(d, redact)
    ss = getSampleStyleSheet()
    body = ParagraphStyle("b", parent=ss["BodyText"], fontSize=9.5, leading=13)
    cell = ParagraphStyle("c", parent=body, fontSize=8.5, leading=11)
    banner = ParagraphStyle(
        "banner",
        parent=body,
        textColor=colors.HexColor("#b00020"),
        fontName="Helvetica-Bold",
        fontSize=10.5,
        leading=14,
    )

    def on_page(canvas, doc):  # type: ignore[no-untyped-def]
        canvas.saveState()
        canvas.setFont("Helvetica-Bold", 8)
        canvas.setFillColor(colors.HexColor("#b00020"))
        canvas.drawString(18 * mm, 10 * mm, "DRAFT - not filed. " + DRAFT_BANNER[:95])
        canvas.drawRightString(A4[0] - 18 * mm, 10 * mm, f"Page {doc.page}")
        if d.simulation:
            canvas.setFont("Helvetica-Bold", 64)
            canvas.setFillColor(colors.Color(0.8, 0.1, 0.1, alpha=0.12))
            canvas.translate(A4[0] / 2, A4[1] / 2)
            canvas.rotate(35)
            canvas.drawCentredString(0, 0, "SIMULATION")
        canvas.restoreState()

    story: list[Any] = []
    lines = md.split("\n")
    i = 0
    while i < len(lines):
        ln = lines[i]
        if ln.startswith("# "):
            story += [Paragraph(_inline(ln[2:]), ss["Title"])]
        elif ln.startswith("## "):
            story += [Spacer(1, 6), Paragraph(_inline(ln[3:]), ss["Heading3"])]
        elif ln.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].startswith("|"):
                if not set(lines[i].replace("|", "").strip()) <= {"-", " "}:
                    rows.append(
                        [
                            Paragraph(_inline(c.strip()), cell)
                            for c in lines[i].strip("|").split("|")
                        ]
                    )
                i += 1
            i -= 1
            t = Table(rows, repeatRows=1)
            t.setStyle(
                TableStyle(
                    [
                        ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eeeeee")),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ]
                )
            )
            story += [t]
        elif ln.startswith("**DRAFT") or ln.startswith("**SIMULATION") or ln.startswith("> **SIM"):
            story += [Paragraph(_inline(ln.lstrip("> ")), banner)]
        elif re.match(r"^(- |\d+\. )", ln):
            items = []
            while i < len(lines) and re.match(r"^(- |\d+\. |  - )", lines[i]):
                items.append(
                    ListItem(
                        Paragraph(_inline(re.sub(r"^\s*(- |\d+\. )(\[ \] )?", "", lines[i])), body)
                    )
                )
                i += 1
            i -= 1
            story += [ListFlowable(items, bulletType="bullet", start="•", leftIndent=12)]
        elif ln.strip() and ln.strip() != "---":
            story += [Paragraph(_inline(ln), body)]
        i += 1

    buf = io.BytesIO()
    SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=16 * mm,
        bottomMargin=18 * mm,
        title="Cyber crime complaint - DRAFT",
        author="SCAM-KHEL (draft generator)",
    ).build(story, onFirstPage=on_page, onLaterPages=on_page)
    return buf.getvalue()
