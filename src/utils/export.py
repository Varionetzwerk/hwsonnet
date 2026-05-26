"""Export hardware data to JSON, TXT and PDF."""

from __future__ import annotations

import json
import datetime
from pathlib import Path
from typing import Any

from src.utils.logger import logger


def export_json(data: dict[str, Any], path: Path) -> bool:
    try:
        path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")
        logger.info("JSON exported to %s", path)
        return True
    except OSError as exc:
        logger.error("JSON export failed: %s", exc)
        return False


def export_txt(data: dict[str, Any], path: Path) -> bool:
    lines: list[str] = [
        "=" * 60,
        "  HWSonnet — System Information Report",
        f"  Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "=" * 60,
        "",
    ]

    def _section(title: str, items: dict[str, Any]) -> None:
        lines.append(f"[ {title} ]")
        lines.append("-" * 40)
        for k, v in items.items():
            lines.append(f"  {k:<28} {v}")
        lines.append("")

    for section, values in data.items():
        if isinstance(values, dict):
            _section(section.upper(), values)
        else:
            lines.append(f"{section}: {values}")

    try:
        path.write_text("\n".join(lines), encoding="utf-8")
        logger.info("TXT exported to %s", path)
        return True
    except OSError as exc:
        logger.error("TXT export failed: %s", exc)
        return False


def export_pdf(data: dict[str, Any], path: Path) -> bool:
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib.units import cm
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

        doc = SimpleDocTemplate(str(path), pagesize=A4)
        styles = getSampleStyleSheet()
        story = []

        story.append(Paragraph("HWSonnet — System Information Report", styles["Title"]))
        story.append(
            Paragraph(
                f"Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                styles["Normal"],
            )
        )
        story.append(Spacer(1, 0.5 * cm))

        for section, values in data.items():
            story.append(Paragraph(section.upper(), styles["Heading2"]))
            if isinstance(values, dict):
                table_data = [["Property", "Value"]] + [
                    [str(k), str(v)] for k, v in values.items()
                ]
                tbl = Table(table_data, colWidths=[8 * cm, 9 * cm])
                tbl.setStyle(
                    TableStyle(
                        [
                            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1c2128")),
                            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#30363d")),
                            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f6f8fa")]),
                        ]
                    )
                )
                story.append(tbl)
            story.append(Spacer(1, 0.3 * cm))

        doc.build(story)
        logger.info("PDF exported to %s", path)
        return True
    except ImportError:
        logger.warning("reportlab not installed — PDF export unavailable")
        return False
    except Exception as exc:
        logger.error("PDF export failed: %s", exc)
        return False
