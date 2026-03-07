"""
PDF carnets — dos temas visuales disponibles

Tema "educamadrid":
  - Header navy (#003370), franja azul (#0065BD), puntos de colores,
    lápiz decorativo, footer "Comunidad de Madrid · EducaMadrid"

Tema "ceip":
  - Header verde bosque (#1A5C38), franja verde (#2D6A4F), puntos de
    colores, footer "CEIPSO Ángel González · Legánés"

Formato: 85×54 mm (tarjeta de crédito), 2 columnas × 5 filas por A4
"""

import io
import os

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas as pdf_canvas

# ── Formato de página ───────────────────────────────────────────
CARD_W = 85 * mm
CARD_H = 54 * mm
COLS = 2
ROWS = 5

PAGE_W, PAGE_H = A4
MARGIN_X = (PAGE_W - COLS * CARD_W) / 2
MARGIN_Y = (PAGE_H - ROWS * CARD_H) / 2

# ── Proporciones internas ──────────────────────────────────
HEADER_H = 11 * mm
FOOTER_H = 4.5 * mm
STRIPE_W = 4 * mm  # franja izquierda (más ancha para los puntos)
QR_MARGIN = 2.5 * mm
CORNER_R = 2 * mm

_CONTENT_H = CARD_H - HEADER_H - FOOTER_H
QR_SIZE = _CONTENT_H - 2 * QR_MARGIN

# ── Definición de temas ──────────────────────────────────
THEMES = {
    "educamadrid": {
        "header": colors.HexColor("#003370"),
        "header_dark": colors.HexColor("#002457"),
        "primary": colors.HexColor("#0065BD"),
        "primary_light": colors.HexColor("#E8F2FB"),
        "footer_text": "Comunidad de Madrid \u00b7 EducaMadrid",
        "school_name": "Material del Aula",
    },
    "ceip": {
        "header": colors.HexColor("#1A5C38"),
        "header_dark": colors.HexColor("#124A2C"),
        "primary": colors.HexColor("#2D6A4F"),
        "primary_light": colors.HexColor("#E5F3EB"),
        "footer_text": "CEIPSO \u00c1ngel Gonz\u00e1lez \u00b7 Leg\u00e1n\u00e9s",
        "school_name": "CEIPSO \u00c1ngel Gonz\u00e1lez",
    },
}

WHITE = colors.white

# Colores decorativos (educación primaria: colores puros)
DOT_RED = colors.HexColor("#E63946")
DOT_YELLOW = colors.HexColor("#F9C846")
DOT_GREEN = colors.HexColor("#52B788")

# Lápiz
P_YELLOW = colors.HexColor("#F9C846")
P_WOOD = colors.HexColor("#DDA96B")
P_ERASER = colors.HexColor("#F4A0A0")
P_BAND = colors.HexColor("#A8B8C8")
P_DARK = colors.HexColor("#555555")


def _pencil(c: pdf_canvas.Canvas, cx: float, cy: float, h: float) -> None:
    """
    Dibuja un lápiz vertical con la punta hacia abajo.
    cx, cy = centro-inferior del lápiz. h = altura total.
    """
    w = h * 0.32
    tip_h = h * 0.22
    body_h = h * 0.53
    band_h = h * 0.07
    eraser_h = h * 0.18
    half_w = w / 2

    # Goma (arriba, redondeada)
    c.setFillColor(P_ERASER)
    c.roundRect(
        cx - half_w, cy + tip_h + body_h + band_h, w, eraser_h, half_w * 0.3, stroke=0, fill=1
    )

    # Cinta metálica
    c.setFillColor(P_BAND)
    c.rect(cx - half_w, cy + tip_h + body_h, w, band_h, stroke=0, fill=1)

    # Cuerpo amarillo
    c.setFillColor(P_YELLOW)
    c.rect(cx - half_w, cy + tip_h, w, body_h, stroke=0, fill=1)

    # Faceta central
    c.setStrokeColor(colors.HexColor("#D4A820"))
    c.setLineWidth(0.5)
    c.line(cx, cy + tip_h + 1, cx, cy + tip_h + body_h - 1)

    # Cono de madera
    c.setFillColor(P_WOOD)
    path = c.beginPath()
    path.moveTo(cx, cy)
    path.lineTo(cx - half_w, cy + tip_h)
    path.lineTo(cx + half_w, cy + tip_h)
    path.close()
    c.drawPath(path, stroke=0, fill=1)

    # Grafito (punta oscura)
    c.setFillColor(P_DARK)
    path2 = c.beginPath()
    path2.moveTo(cx, cy)
    path2.lineTo(cx - half_w * 0.18, cy + tip_h * 0.32)
    path2.lineTo(cx + half_w * 0.18, cy + tip_h * 0.32)
    path2.close()
    c.drawPath(path2, stroke=0, fill=1)


def _draw_card(c: pdf_canvas.Canvas, x: float, y: float, usuario, th: dict) -> None:
    NAVY = th["header"]
    BLUE = th["primary"]
    BLUE_LIGHT = th["primary_light"]

    # — 1. Fondo navy redondeado (da esquinas correctas al header) —
    c.setFillColor(NAVY)
    c.roundRect(x, y, CARD_W, CARD_H, CORNER_R, stroke=0, fill=1)

    # — 2. Área de contenido + footer (blanco, cubre el navy inferior) —
    c.setFillColor(WHITE)
    c.rect(x, y, CARD_W, CARD_H - HEADER_H, stroke=0, fill=1)

    # — 3. Footer azul claro —
    c.setFillColor(BLUE_LIGHT)
    c.rect(x, y, CARD_W, FOOTER_H, stroke=0, fill=1)

    # — 4. Franja vertical izquierda (azul) —
    c.setFillColor(BLUE)
    c.rect(x, y, STRIPE_W, _CONTENT_H + FOOTER_H, stroke=0, fill=1)

    # Tres puntos de colores primarios en la franja
    dot_r = STRIPE_W * 0.27
    dot_cx = x + STRIPE_W / 2
    base_y = y + FOOTER_H
    for dot_color, frac in [
        (DOT_RED, 0.75),
        (DOT_YELLOW, 0.50),
        (DOT_GREEN, 0.25),
    ]:
        c.setFillColor(dot_color)
        c.circle(dot_cx, base_y + _CONTENT_H * frac, dot_r, stroke=0, fill=1)

    # — 5. Texto del header —
    header_y = y + CARD_H - HEADER_H
    c.setFillColor(WHITE)
    c.setFont("Helvetica-Bold", 7.2)
    c.drawString(
        x + STRIPE_W + 3 * mm,
        header_y + HEADER_H / 2 - 2.5,
        th["school_name"],
    )
    c.setFont("Helvetica", 6.5)
    c.drawRightString(
        x + CARD_W - 2.5 * mm,
        header_y + HEADER_H / 2 - 2.5,
        usuario.codigo_qr or "",
    )

    # — 6. Texto del footer —
    c.setFillColor(BLUE)
    c.setFont("Helvetica", 4.8)
    c.drawString(
        x + STRIPE_W + 2.5 * mm,
        y + 1.5 * mm,
        th["footer_text"],
    )

    # — 7. Código QR —
    content_y0 = y + FOOTER_H
    qr_x = x + STRIPE_W + QR_MARGIN
    qr_y = content_y0 + (_CONTENT_H - QR_SIZE) / 2
    qr_path = os.path.join("./static/qr_usuarios", f"{usuario.codigo_qr}.png")
    if os.path.exists(qr_path):
        c.drawImage(
            qr_path,
            qr_x,
            qr_y,
            width=QR_SIZE,
            height=QR_SIZE,
            preserveAspectRatio=True,
        )

    # — 8. Apellido y nombre —
    text_x = qr_x + QR_SIZE + 2.5 * mm
    mid_y = content_y0 + _CONTENT_H / 2

    apellido = (usuario.apellido or "").upper()
    nombre = usuario.nombre or ""

    afs = 10 if len(apellido) <= 11 else 8 if len(apellido) <= 15 else 6.5
    c.setFillColor(NAVY)
    c.setFont("Helvetica-Bold", afs)
    c.drawString(text_x, mid_y + 1.5 * mm, apellido[:18])

    c.setFillColor(BLUE)
    c.setFont("Helvetica", 8)
    c.drawString(text_x, mid_y - 3.5 * mm, nombre[:20])

    # — 9. Lápiz decorativo (esquina inferior derecha del contenido) —
    pencil_h = 11 * mm
    pencil_cx = x + CARD_W - 5.5 * mm
    pencil_cy = content_y0 + 1.5 * mm
    _pencil(c, pencil_cx, pencil_cy, pencil_h)

    # — 10. Borde final encima de todo —
    c.setStrokeColor(BLUE)
    c.setLineWidth(0.8)
    c.roundRect(x, y, CARD_W, CARD_H, CORNER_R, stroke=1, fill=0)


def generate_pdf_carnets(usuarios: list, theme: str = "educamadrid") -> bytes:
    """Acepta una lista de objetos ORM Usuario y el tema visual. Devuelve el PDF como bytes."""
    th = THEMES.get(theme, THEMES["educamadrid"])
    buf = io.BytesIO()
    c = pdf_canvas.Canvas(buf, pagesize=A4)

    per_page = COLS * ROWS
    for page_start in range(0, len(usuarios), per_page):
        page_users = usuarios[page_start : page_start + per_page]
        for i, usuario in enumerate(page_users):
            col = i % COLS
            row = i // COLS
            cx = MARGIN_X + col * CARD_W
            cy = PAGE_H - MARGIN_Y - (row + 1) * CARD_H
            _draw_card(c, cx, cy, usuario, th)
        if page_start + per_page < len(usuarios):
            c.showPage()

    c.save()
    return buf.getvalue()
