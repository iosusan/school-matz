import os
from pathlib import Path

import qrcode
from PIL import Image, ImageDraw, ImageFont

from backend.config import settings

QR_USUARIOS_DIR = "./static/qr_usuarios"


def _ensure_dir():
    Path(settings.qr_images_dir).mkdir(parents=True, exist_ok=True)


def _ensure_usuarios_dir():
    Path(QR_USUARIOS_DIR).mkdir(parents=True, exist_ok=True)


def _make_qr_image(url: str, box_size: int = 10) -> Image.Image:
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=box_size,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)
    return qr.make_image(fill_color="black", back_color="white").convert("RGB")


def _load_fonts(big: int = 18, small: int = 14):
    try:
        return (
            ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", big),
            ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", small),
        )
    except OSError:
        default = ImageFont.load_default()
        return default, default


def generate_qr_image(codigo_qr: str, descripcion: str, categoria_nombre: str | None = None) -> str:
    """
    Genera una imagen PNG con el QR y texto descriptivo para material.
    Devuelve la ruta relativa al fichero generado.
    """
    _ensure_dir()

    url = f"{settings.qr_base_url}/scan/{codigo_qr}"
    qr_img = _make_qr_image(url)
    qr_w, qr_h = qr_img.size

    text_area_h = 80
    canvas = Image.new("RGB", (qr_w, qr_h + text_area_h), "white")
    canvas.paste(qr_img, (0, 0))

    draw = ImageDraw.Draw(canvas)
    font_big, font_small = _load_fonts(18, 14)

    y = qr_h + 8
    draw.text((qr_w // 2, y), codigo_qr, font=font_big, fill="black", anchor="mt")
    y += 26
    short_desc = descripcion[:35] + "…" if len(descripcion) > 35 else descripcion
    draw.text((qr_w // 2, y), short_desc, font=font_small, fill="#444", anchor="mt")
    if categoria_nombre:
        y += 22
        draw.text((qr_w // 2, y), categoria_nombre, font=font_small, fill="#888", anchor="mt")

    filename = f"{codigo_qr}.png"
    filepath = os.path.join(settings.qr_images_dir, filename)
    canvas.save(filepath)
    return filepath


def generate_qr_usuario(usuario_id: int, uuid4_token: str, nombre: str, apellido: str) -> str:
    """
    Genera una imagen PNG con el QR personal del usuario.
    El QR codifica el token UUID4 (nunca se almacena en claro en la BD).
    Devuelve la ruta al fichero generado.
    """
    _ensure_usuarios_dir()

    url = f"{settings.qr_base_url}/usuario/{uuid4_token}"
    qr_img = _make_qr_image(url, box_size=10)
    qr_w, qr_h = qr_img.size

    text_area_h = 60
    canvas = Image.new("RGB", (qr_w, qr_h + text_area_h), "white")
    canvas.paste(qr_img, (0, 0))

    draw = ImageDraw.Draw(canvas)
    font_big, font_small = _load_fonts(18, 14)

    y = qr_h + 8
    draw.text((qr_w // 2, y), apellido, font=font_big, fill="black", anchor="mt")
    y += 26
    draw.text((qr_w // 2, y), nombre, font=font_small, fill="#444", anchor="mt")

    filepath = os.path.join(QR_USUARIOS_DIR, f"usuario_{usuario_id}.png")
    canvas.save(filepath)
    return filepath
