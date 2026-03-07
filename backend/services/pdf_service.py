"""
Genera un PDF con etiquetas QR en formato de cuadrícula (3×N) listas para imprimir.
Cada etiqueta incluye el QR, el código y la descripción.
"""

import contextlib
import io
import os
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas as pdf_canvas

from backend.config import settings
from backend.services.qr_service import generate_qr_image

# Dimensiones de etiqueta (ajustables)
LABEL_W = 60 * mm
LABEL_H = 70 * mm
COLS = 3
PAGE_W, PAGE_H = A4
MARGIN_X = (PAGE_W - COLS * LABEL_W) / 2
MARGIN_TOP = 15 * mm


def generar_pdf_etiquetas(materiales: list) -> bytes:
    """
    Recibe una lista de objetos Material (SQLAlchemy) y devuelve un PDF en bytes.
    """
    buf = io.BytesIO()
    c = pdf_canvas.Canvas(buf, pagesize=A4)

    filas_por_pagina = int((PAGE_H - MARGIN_TOP * 2) // LABEL_H)
    labels_por_pagina = COLS * filas_por_pagina

    for idx, mat in enumerate(materiales):
        page_idx = idx % labels_por_pagina
        if page_idx == 0 and idx > 0:
            c.showPage()

        col = page_idx % COLS
        row = page_idx // COLS

        x = MARGIN_X + col * LABEL_W
        y = PAGE_H - MARGIN_TOP - (row + 1) * LABEL_H

        _dibujar_etiqueta(c, x, y, mat)

    c.save()
    buf.seek(0)
    return buf.read()


def _dibujar_etiqueta(c: pdf_canvas.Canvas, x: float, y: float, mat) -> None:
    # Borde
    c.setStrokeColor(colors.Color(0.85, 0.85, 0.85))
    c.setLineWidth(0.5)
    c.rect(x, y, LABEL_W, LABEL_H)

    # QR image — se genera si no existe
    qr_path = os.path.join(settings.qr_images_dir, f"{mat.codigo_qr}.png")
    if not Path(qr_path).exists():
        cat = mat.categoria.nombre if mat.categoria else None
        generate_qr_image(mat.codigo_qr, mat.descripcion, cat)

    qr_size = 44 * mm
    qr_x = x + (LABEL_W - qr_size) / 2
    qr_y = y + LABEL_H - qr_size - 4 * mm
    with contextlib.suppress(Exception):
        c.drawImage(ImageReader(qr_path), qr_x, qr_y, width=qr_size, height=qr_size)

    # Código QR (texto)
    c.setFont("Helvetica-Bold", 7)
    c.setFillColor(colors.black)
    c.drawCentredString(x + LABEL_W / 2, qr_y - 5 * mm, mat.codigo_qr)

    # Descripción — truncada si es muy larga, puede ocupar 2 líneas
    c.setFont("Helvetica", 7)
    c.setFillColor(colors.Color(0.3, 0.3, 0.3))
    desc = mat.descripcion
    max_chars = 30
    if len(desc) <= max_chars:
        c.drawCentredString(x + LABEL_W / 2, qr_y - 9 * mm, desc)
    else:
        # Partir en dos líneas
        pivot = desc[:max_chars].rfind(" ")
        pivot = pivot if pivot > 0 else max_chars
        c.drawCentredString(x + LABEL_W / 2, qr_y - 9 * mm, desc[:pivot].strip())
        c.drawCentredString(x + LABEL_W / 2, qr_y - 13 * mm, desc[pivot:].strip()[:max_chars])

    # Categoría (si existe)
    if mat.categoria:
        c.setFont("Helvetica", 6)
        c.setFillColor(colors.Color(0.55, 0.55, 0.55))
        c.drawCentredString(x + LABEL_W / 2, qr_y - 17 * mm, mat.categoria.nombre[:35])
