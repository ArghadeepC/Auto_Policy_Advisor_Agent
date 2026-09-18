from pathlib import Path

from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer,
)
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet


OUTPUT_DIR = Path(__file__).resolve().parents[2] / "output" / "receipts"


def create_payment_receipt_pdf(
    Transaction_ID: str,
    Customer_ID: str,
    Policy_ID: str,
    CustomerName: str,
    Vehicle: str,
    VIN: str,
    PlateNumber: str,
    License: str,
    Address: str,
    PolicyType: str,
    PaymentMethod: str,
    PaymentAmount: float,
    PaymentStatus: str,
    PaymentDateTime: str,
):
    try:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

        filename = f"receipt_{Transaction_ID}.pdf"
        path = OUTPUT_DIR / filename

        doc = SimpleDocTemplate(
            str(path),
            pagesize=letter,
        )

        styles = getSampleStyleSheet()

        elements = [
            Paragraph(
                "Insurance Payment Receipt",
                styles["Title"],
            ),
            Spacer(1, 20),
        ]

        data = [
            ["Field", "Value"],
            ["Transaction ID", Transaction_ID],
            ["Customer ID", Customer_ID],
            ["Policy ID", Policy_ID],
            ["Customer Name", CustomerName],
            ["Vehicle", Vehicle],
            ["Vehicle Number", VIN],
            ["Plate Number", PlateNumber],
            ["License", License],
            ["Address", Address],
            ["Policy Type", PolicyType],
            ["Payment Method", PaymentMethod],
            ["Payment Amount", f"${PaymentAmount:.2f}"],
            ["Payment Status", PaymentStatus],
            ["Payment DateTime", PaymentDateTime],
        ]

        table = Table(
            data,
            colWidths=[150, 300],
        )

        table.setStyle(
            TableStyle([
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.lightgrey,
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.black,
                ),
                (
                    "ALIGN",
                    (0, 0),
                    (-1, -1),
                    "LEFT",
                ),
            ])
        )

        elements.extend([
            table,
            Spacer(1, 20),
            Paragraph(
                "© 2026 XYZ Insurance Firm. Local capstone demo.",
                styles["Normal"],
            ),
        ])

        doc.build(elements)

        return {
            "success": True,
            "filename": filename,
            "local_path": str(path),
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }