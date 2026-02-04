## OCR (Validación de etiquetas) – Entorno de Planta

Este proyecto incluye OCR para validar/identificar producto/OT/orden desde etiquetas impresas o documentos de embarque.

### Backend (Docker recomendado)
- El contenedor del backend instala `tesseract-ocr` y data `spa`/`eng` automáticamente.
- En `config.yaml`:
  - `ocr.enabled: true`
  - `ocr.languages: "spa+eng"`

### Backend (Windows local)
1. Instala Tesseract OCR en Windows.
2. Configura la ruta en `config.yaml`:
   - `ocr.tesseract_cmd: "C:/Program Files/Tesseract-OCR/tesseract.exe"`
3. Reinicia el backend.

### Endpoints
- Producción (validación contra Orden/Items/OT):
  - `POST /api/production/order/<order_id>/ocr-validate` (multipart `image`)
- Logística (validación contra Orden/Cliente):
  - `POST /api/logistics/shipment/<order_id>/ocr-validate` (multipart `image`)

### Frontend (uso en tablets/handhelds)
- En Producción y Logística se habilitó captura desde cámara usando `capture="environment"`.
- Flujo recomendado:
  1) Selecciona la orden.
  2) Captura foto de la etiqueta.
  3) Ejecuta “Validar con OCR” y verifica chips “OK/No coincide”.

### Recomendaciones de planta
- Etiquetas con alto contraste y fuente ≥ 10pt.
- Evitar reflejos (laminados), usar iluminación uniforme.
- En tablets: mantener la etiqueta centrada y llenar el encuadre.