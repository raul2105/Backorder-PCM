from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from typing import Optional, Tuple

from flask import current_app


class OCRNotAvailable(RuntimeError):
    pass


@dataclass
class OcrOutput:
    text: str
    avg_confidence: Optional[float]


def _get_ocr_config() -> dict:
    cfg = current_app.config.get('OCR_CONFIG') if current_app else None
    return cfg or {}


def is_ocr_enabled() -> bool:
    cfg = _get_ocr_config()
    return bool(cfg.get('enabled', False))


def _import_deps():
    try:
        import pytesseract  # type: ignore
        from PIL import Image, ImageOps  # type: ignore
    except Exception as exc:
        raise OCRNotAvailable(
            'Dependencias de OCR no disponibles. Instala pytesseract y Pillow.'
        ) from exc

    return pytesseract, Image, ImageOps


def _configure_tesseract(pytesseract_module) -> None:
    cfg = _get_ocr_config()
    tesseract_cmd = (cfg.get('tesseract_cmd') or '').strip()
    if tesseract_cmd:
        pytesseract_module.pytesseract.tesseract_cmd = tesseract_cmd


def _preprocess_image(image_bytes: bytes):
    pytesseract, Image, ImageOps = _import_deps()

    try:
        img = Image.open(BytesIO(image_bytes))
    except Exception as exc:
        raise ValueError('No se pudo abrir la imagen enviada') from exc

    img = ImageOps.exif_transpose(img)
    img = img.convert('L')

    # Aumentar tamaño para mejorar OCR en etiquetas pequeñas
    w, h = img.size
    scale = 2 if max(w, h) < 1600 else 1
    if scale != 1:
        img = img.resize((w * scale, h * scale))

    img = ImageOps.autocontrast(img)

    # Umbral simple (sin OpenCV) para binarizar
    img = img.point(lambda p: 255 if p > 170 else 0)

    return img


def _ocr_with_confidence(img) -> Tuple[str, Optional[float]]:
    pytesseract, _, _ = _import_deps()
    _configure_tesseract(pytesseract)

    cfg = _get_ocr_config()
    lang = (cfg.get('languages') or 'spa+eng').strip()

    # PSM 6: bloque uniforme de texto (suele funcionar bien con etiquetas)
    oem = int(cfg.get('oem', 3))
    psm = int(cfg.get('psm', 6))
    config = f"--oem {oem} --psm {psm}"

    try:
        data = pytesseract.image_to_data(img, lang=lang, config=config, output_type=pytesseract.Output.DICT)
        text = pytesseract.image_to_string(img, lang=lang, config=config)
    except Exception as exc:
        raise OCRNotAvailable(
            'OCR falló. Verifica que Tesseract esté instalado y accesible.'
        ) from exc

    conf_values = []
    if isinstance(data, dict) and 'conf' in data:
        for c in data.get('conf', []):
            try:
                c_float = float(c)
            except Exception:
                continue
            if c_float >= 0:
                conf_values.append(c_float)

    avg_conf = None
    if conf_values:
        avg_conf = sum(conf_values) / len(conf_values)

    return (text or '').strip(), avg_conf


def run_ocr(image_bytes: bytes) -> OcrOutput:
    if not is_ocr_enabled():
        raise OCRNotAvailable('OCR no está habilitado en la configuración')

    img = _preprocess_image(image_bytes)
    text, avg_conf = _ocr_with_confidence(img)

    if not text:
        return OcrOutput(text='', avg_confidence=avg_conf)

    # Normalizar saltos para facilitar matching
    text = '\n'.join([line.strip() for line in text.splitlines() if line.strip()])
    return OcrOutput(text=text, avg_confidence=avg_conf)
