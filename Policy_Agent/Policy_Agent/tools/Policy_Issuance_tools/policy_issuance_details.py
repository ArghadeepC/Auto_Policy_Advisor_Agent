from pathlib import Path
import datetime

from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer,
    PageBreak,
)
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch


OUTPUT_DIR = Path(__file__).resolve().parents[2] / "output" / "policies"


def add_header_footer(canvas_obj, doc):
    canvas_obj.setFont("Helvetica", 9)
    canvas_obj.drawRightString(
        7.9 * inch,
        10.7 * inch,
        datetime.datetime.now().strftime("%B %d, %Y"),
    )

    canvas_obj.saveState()
    canvas_obj.setFont("Helvetica-Bold", 60)
    canvas_obj.setFillGray(0.9, 0.3)
    canvas_obj.rotate(45)
    canvas_obj.drawCentredString(300, 100, "XYZ INSURANCE")
    canvas_obj.restoreState()

    canvas_obj.setFont("Helvetica-Oblique", 8)
    canvas_obj.drawCentredString(
        4.25 * inch,
        0.5 * inch,
        "© 2026 XYZ Insurance Firm. Local capstone demo.",
    )


def policy_pdf_details(
    policy_details: dict,
    vehicle_details: dict,
    driver_details: dict,
) -> dict:

    try:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

        policy_number = policy_details.get(
            "policy_number",
            policy_details.get("Policy_ID", "NA"),
        )

        # Keep the filename safe
        policy_number = str(policy_number).replace("/", "_").replace("\\", "_")

        path = OUTPUT_DIR / f"policy_{policy_number}.pdf"

        doc = SimpleDocTemplate(
            str(path),
            pagesize=letter,
        )

        styles = getSampleStyleSheet()
        elements = []

        sections = [
            ("Insurance Policy Document", policy_details),
            ("Vehicle Details", vehicle_details),
            ("Driver Details", driver_details),
        ]

        for title, details in sections:

            elements.append(
                Paragraph(
                    title,
                    styles["Title"],
                )
            )

            elements.append(Spacer(1, 20))

            data = [["Field", "Value"]]

            for key, value in (details or {}).items():
                data.append(
                    [
                        str(key).replace("_", " ").title(),
                        str(value),
                    ]
                )

            table = Table(
                data,
                colWidths=[250, 320],
            )

            table.setStyle(
                TableStyle(
                    [
                        (
                            "BACKGROUND",
                            (0, 0),
                            (-1, 0),
                            colors.HexColor("#003366"),
                        ),
                        (
                            "TEXTCOLOR",
                            (0, 0),
                            (-1, 0),
                            colors.white,
                        ),
                        (
                            "GRID",
                            (0, 0),
                            (-1, -1),
                            0.5,
                            colors.black,
                        ),
                        (
                            "FONTSIZE",
                            (0, 0),
                            (-1, -1),
                            10,
                        ),
                        (
                            "VALIGN",
                            (0, 0),
                            (-1, -1),
                            "TOP",
                        ),
                    ]
                )
            )

            elements.append(table)

            if title != "Driver Details":
                elements.append(PageBreak())

        doc.build(
            elements,
            onFirstPage=add_header_footer,
            onLaterPages=add_header_footer,
        )

        return {
            "success": True,
            "filename": path.name,
            "local_path": str(path),
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


policy_pdf_tool = policy_pdf_details