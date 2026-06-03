# Copyright (c) 2025-2026 MKM Research Labs. All rights reserved.

"""PDF report builder with MKM branding for audit reports."""

from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm, cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable,
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT


# MKM brand colours (hex values centralised in config.py)
from config import (
    MKM_DARK_HEX, MKM_BLUE_HEX, MKM_LIGHT_BLUE_HEX, MKM_GREEN_HEX,
    MKM_RED_HEX, MKM_AMBER_HEX, MKM_GREY_HEX, MKM_LIGHT_GREY_HEX
)

MKM_DARK = colors.HexColor(MKM_DARK_HEX)
MKM_BLUE = colors.HexColor(MKM_BLUE_HEX)
MKM_LIGHT_BLUE = colors.HexColor(MKM_LIGHT_BLUE_HEX)
MKM_GREEN = colors.HexColor(MKM_GREEN_HEX)
MKM_RED = colors.HexColor(MKM_RED_HEX)
MKM_AMBER = colors.HexColor(MKM_AMBER_HEX)
MKM_GREY = colors.HexColor(MKM_GREY_HEX)
MKM_LIGHT_GREY = colors.HexColor(MKM_LIGHT_GREY_HEX)

PAGE_W, PAGE_H = A4


def _status_color(status: str) -> colors.Color:
    s = status.upper()
    if s in ("OK", "PASS", "100.0%"):
        return MKM_GREEN
    elif s in ("FAIL", "HIGH"):
        return MKM_RED
    elif s in ("MEDIUM", "REVIEW", "WARNING"):
        return MKM_AMBER
    return MKM_GREY


class MKMReportBuilder:
    """Builds branded MKM PDF reports."""

    def __init__(self, output_path: str, title: str, subtitle: str = ""):
        self.output_path = output_path
        self.title = title
        self.subtitle = subtitle
        self.elements = []
        self._setup_styles()

    def _setup_styles(self):
        self.styles = getSampleStyleSheet()
        self.styles.add(ParagraphStyle(
            "MKMTitle", parent=self.styles["Title"],
            fontSize=22, textColor=MKM_DARK, spaceAfter=6,
        ))
        self.styles.add(ParagraphStyle(
            "MKMSubtitle", parent=self.styles["Normal"],
            fontSize=11, textColor=MKM_GREY, spaceAfter=16,
        ))
        self.styles.add(ParagraphStyle(
            "MKMHeading", parent=self.styles["Heading1"],
            fontSize=14, textColor=MKM_DARK, spaceBefore=16, spaceAfter=8,
        ))
        self.styles.add(ParagraphStyle(
            "MKMBody", parent=self.styles["Normal"],
            fontSize=9, textColor=MKM_DARK, spaceAfter=6, leading=13,
        ))
        self.styles.add(ParagraphStyle(
            "MKMSmall", parent=self.styles["Normal"],
            fontSize=7.5, textColor=MKM_GREY, spaceAfter=4,
        ))
        self.styles.add(ParagraphStyle(
            "MKMMetric", parent=self.styles["Normal"],
            fontSize=24, textColor=MKM_BLUE, alignment=TA_CENTER,
        ))

    def add_cover_page(self, metrics: List[Dict[str, str]]):
        """Add a cover page with title, date, and headline metrics."""
        self.elements.append(Spacer(1, 40 * mm))
        self.elements.append(Paragraph("MKM Research Labs", self.styles["MKMSubtitle"]))
        self.elements.append(Paragraph(self.title, self.styles["MKMTitle"]))
        if self.subtitle:
            self.elements.append(Paragraph(self.subtitle, self.styles["MKMSubtitle"]))

        date_str = datetime.now().strftime("%d %B %Y")
        self.elements.append(Paragraph(
            f"Report Date: {date_str}", self.styles["MKMBody"]
        ))
        self.elements.append(Paragraph(
            "Governance Framework: SR 11-7 / SS1/23 Model Risk Management",
            self.styles["MKMSmall"],
        ))
        self.elements.append(Spacer(1, 15 * mm))

        # Headline metric boxes
        if metrics:
            metric_data = [[m.get("label", "") for m in metrics]]
            metric_values = [[m.get("value", "") for m in metrics]]
            combined = metric_values + metric_data

            t = Table(combined, colWidths=[45 * mm] * len(metrics))
            t.setStyle(TableStyle([
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("FONTSIZE", (0, 0), (-1, 0), 18),
                ("FONTSIZE", (0, 1), (-1, 1), 8),
                ("TEXTCOLOR", (0, 0), (-1, 0), MKM_BLUE),
                ("TEXTCOLOR", (0, 1), (-1, 1), MKM_GREY),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]))
            self.elements.append(t)

        self.elements.append(PageBreak())

    def add_heading(self, text: str, level: int = 1):
        style = "MKMHeading" if level == 1 else "MKMBody"
        prefix = f"{level}. " if level >= 1 else ""
        self.elements.append(Paragraph(f"{prefix}{text}", self.styles[style]))

    def add_text(self, text: str, style: str = "MKMBody"):
        self.elements.append(Paragraph(text, self.styles[style]))

    def add_spacer(self, height_mm: float = 5):
        self.elements.append(Spacer(1, height_mm * mm))

    def add_hr(self):
        self.elements.append(HRFlowable(
            width="100%", thickness=0.5, color=MKM_LIGHT_GREY,
            spaceAfter=8, spaceBefore=8,
        ))

    def add_metric_table(self, rows: List[Dict[str, str]]):
        """Add a Metric/Value/Status table (like the executive summary)."""
        header = ["Metric", "Value", "Status"]
        data = [header]
        for row in rows:
            data.append([row.get("metric", ""), row.get("value", ""), row.get("status", "")])

        t = Table(data, colWidths=[70 * mm, 50 * mm, 30 * mm])
        style = [
            ("BACKGROUND", (0, 0), (-1, 0), MKM_DARK),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTSIZE", (0, 0), (-1, 0), 9),
            ("FONTSIZE", (0, 1), (-1, -1), 8),
            ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
            ("GRID", (0, 0), (-1, -1), 0.5, MKM_LIGHT_GREY),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, MKM_LIGHT_GREY]),
        ]
        # Color-code status column
        for i, row in enumerate(rows, 1):
            sc = _status_color(row.get("status", ""))
            style.append(("TEXTCOLOR", (2, i), (2, i), sc))

        t.setStyle(TableStyle(style))
        self.elements.append(t)
        self.elements.append(Spacer(1, 4 * mm))

    def add_data_table(self, headers: List[str], rows: List[List[str]],
                       col_widths: Optional[List[float]] = None):
        """Add a generic data table."""
        data = [headers] + rows
        if col_widths:
            widths = [w * mm for w in col_widths]
        else:
            avail = 170  # mm
            widths = [avail / len(headers) * mm] * len(headers)

        t = Table(data, colWidths=widths)
        style = [
            ("BACKGROUND", (0, 0), (-1, 0), MKM_DARK),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTSIZE", (0, 0), (-1, 0), 8),
            ("FONTSIZE", (0, 1), (-1, -1), 7.5),
            ("GRID", (0, 0), (-1, -1), 0.5, MKM_LIGHT_GREY),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, MKM_LIGHT_GREY]),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]
        t.setStyle(TableStyle(style))
        self.elements.append(t)
        self.elements.append(Spacer(1, 4 * mm))

    def add_page_break(self):
        self.elements.append(PageBreak())

    def build(self):
        """Generate the PDF."""
        Path(self.output_path).parent.mkdir(parents=True, exist_ok=True)

        doc = SimpleDocTemplate(
            self.output_path,
            pagesize=A4,
            leftMargin=20 * mm,
            rightMargin=20 * mm,
            topMargin=25 * mm,
            bottomMargin=20 * mm,
        )

        doc.build(self.elements, onFirstPage=self._header_footer, onLaterPages=self._header_footer)
        return self.output_path

    def _header_footer(self, canvas, doc):
        """Draw header and footer on every page."""
        canvas.saveState()

        # Header line
        canvas.setStrokeColor(MKM_BLUE)
        canvas.setLineWidth(1.5)
        canvas.line(20 * mm, PAGE_H - 18 * mm, PAGE_W - 20 * mm, PAGE_H - 18 * mm)

        # Header text
        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(MKM_GREY)
        canvas.drawString(20 * mm, PAGE_H - 16 * mm, "MKMChat Document Q&A Platform")

        date_str = datetime.now().strftime("%d %B %Y")
        canvas.drawRightString(PAGE_W - 20 * mm, PAGE_H - 16 * mm, f"{self.title}  |  {date_str}")

        # Footer
        canvas.setFont("Helvetica", 6.5)
        canvas.setFillColor(MKM_GREY)
        canvas.drawString(
            20 * mm, 12 * mm,
            "CONFIDENTIAL \u2014 MKM Research Labs  |  SR 11-7 / SS1/23 Model Governance"
        )
        canvas.drawRightString(PAGE_W - 20 * mm, 12 * mm, f"Page {doc.page}")

        canvas.restoreState()
