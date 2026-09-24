"""Render a printable demo receipt/convocation for one submitted case."""

from io import BytesIO

from reportlab.graphics import renderPDF
from reportlab.graphics.barcode.qr import QrCodeWidget
from reportlab.graphics.shapes import Drawing
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.utils import simpleSplit

from app.services.case_lifecycle import NEXT_ACTIONS, canonical_status, tracking_code

STATUS_LABELS = {
    "DRAFT": "Brouillon",
    "SUBMITTED": "Déposée",
    "UNDER_REVIEW": "En cours d'examen",
    "DOCS_APPROVED": "Pièces validées",
    "READY_FOR_PICKUP": "Prête au retrait",
}


def _qr(canvas: Canvas, value: str, x: float, y: float, size: float = 108) -> None:
    widget = QrCodeWidget(value)
    x0, y0, x1, y1 = widget.getBounds()
    drawing = Drawing(size, size, transform=[size / (x1 - x0), 0, 0, size / (y1 - y0), 0, 0])
    drawing.add(widget)
    renderPDF.draw(drawing, canvas, x, y)


def render_case_receipt(case, next_action: str | None = None) -> bytes:
    """Build a one-page PDF; the QR contains only the public tracking code."""
    buffer = BytesIO()
    canvas = Canvas(buffer, pagesize=A4)
    width, height = A4
    navy = colors.HexColor("#17324D")
    orange = colors.HexColor("#D9623A")
    grey = colors.HexColor("#5B6674")
    code = tracking_code(case.public_id, case.created_at)
    state = canonical_status(case.status)

    canvas.setFillColor(navy)
    canvas.rect(0, height - 120, width, 120, stroke=0, fill=1)
    canvas.setFillColor(colors.white)
    canvas.setFont("Helvetica-Bold", 22)
    canvas.drawString(46, height - 60, "OmniAgent")
    canvas.setFont("Helvetica", 10)
    canvas.drawString(46, height - 80, "Assistant pour les démarches administratives")
    canvas.setFillColor(orange)
    canvas.roundRect(45, height - 161, width - 90, 25, 6, stroke=0, fill=1)
    canvas.setFillColor(colors.white)
    canvas.setFont("Helvetica-Bold", 10)
    canvas.drawCentredString(width / 2, height - 153, "DOCUMENT DE DÉMONSTRATION - NON OFFICIEL")

    title = "Convocation de retrait" if state == "READY_FOR_PICKUP" else "Accusé de réception"
    canvas.setFillColor(navy)
    canvas.setFont("Helvetica-Bold", 19)
    canvas.drawString(46, height - 210, title)
    canvas.setFont("Helvetica", 10)
    canvas.setFillColor(grey)
    canvas.drawString(46, height - 230, "Conservez ce reçu pour suivre votre dossier dans OmniAgent.")

    canvas.setStrokeColor(colors.HexColor("#DCE4EA"))
    canvas.line(46, height - 251, width - 46, height - 251)
    fields = (
        ("Code de suivi", code),
        ("Référence", case.reference_number or code),
        ("Demandeur", case.applicant_name or case.user.full_name or "-"),
        ("Service", case.service.name_fr if case.service else "-"),
        ("Date de dépôt", case.created_at.strftime("%d/%m/%Y %H:%M")),
        ("Statut", STATUS_LABELS.get(state, state.replace("_", " "))),
    )
    y = height - 283
    for label, value in fields:
        canvas.setFont("Helvetica", 10)
        canvas.setFillColor(grey)
        canvas.drawString(46, y, label)
        canvas.setFont("Helvetica-Bold", 11)
        canvas.setFillColor(navy)
        canvas.drawString(174, y, str(value)[:61])
        y -= 37

    canvas.setFillColor(colors.HexColor("#F3F6F8"))
    canvas.roundRect(45, 207, width - 90, 83, 10, stroke=0, fill=1)
    canvas.setFillColor(navy)
    canvas.setFont("Helvetica-Bold", 11)
    canvas.drawString(62, 267, "Prochaine étape")
    canvas.setFont("Helvetica", 10)
    action = next_action or NEXT_ACTIONS.get(state, {}).get("fr", "Consultez votre dossier dans OmniAgent.")
    for index, line in enumerate(simpleSplit(action, "Helvetica", 10, width - 124)[:3]):
        canvas.drawString(62, 246 - index * 15, line)

    _qr(canvas, code, 46, 65)
    canvas.setFillColor(grey)
    canvas.setFont("Helvetica", 9)
    canvas.drawString(171, 145, "QR de démonstration : contient le code de suivi.")
    canvas.drawString(171, 129, "Ce document ne remplace pas une pièce officielle.")
    canvas.setStrokeColor(colors.HexColor("#DCE4EA"))
    canvas.line(46, 53, width - 46, 53)
    canvas.setFont("Helvetica", 8)
    canvas.drawString(46, 36, "OmniAgent | Reçu généré automatiquement")
    canvas.drawRightString(width - 46, 36, "Page 1 / 1")
    canvas.showPage()
    canvas.save()
    return buffer.getvalue()
