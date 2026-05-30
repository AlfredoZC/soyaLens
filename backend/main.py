"""
backend/main.py — Servidor FastAPI de SoyaLens.

Implementa EXACTAMENTE el contrato de API definido en PROJECT.md §5.3.
No inventa campos ni endpoints fuera del contrato.

Endpoints:
    GET  /health
    POST /api/v1/analyze
    GET  /api/v1/samples
    GET  /api/v1/samples/{id}
    GET  /api/v1/stats/today
"""

import sys
import os
import tempfile
from pathlib import Path

# ── Añade la raíz del proyecto al path para poder importar shared/ y ai/ ────
_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from fastapi import FastAPI, File, Form, UploadFile, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

import backend.db as db
from ai.pipeline import detect_grains, summarize, generate_certificate
from shared.schemas import Certificate

# --------------------------------------------------------------------------- #
#  App & CORS
# --------------------------------------------------------------------------- #

app = FastAPI(
    title="SoyaLens API",
    description="Backend del sistema de auditoría visual de granos de soya.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # En producción: restringir al dominio del frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --------------------------------------------------------------------------- #
#  Manejador global de excepciones no controladas
# --------------------------------------------------------------------------- #

@app.exception_handler(Exception)
async def generic_exception_handler(request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"error": str(exc)},
    )


# --------------------------------------------------------------------------- #
#  GET /health
# --------------------------------------------------------------------------- #

@app.get("/health", tags=["sistema"])
def health():
    """Comprueba que el servidor está en pie."""
    return {"status": "ok"}


# --------------------------------------------------------------------------- #
#  POST /api/v1/analyze
# --------------------------------------------------------------------------- #

@app.post("/api/v1/analyze", response_model=Certificate, tags=["análisis"])
async def analyze(
    image: UploadFile = File(..., description="Imagen de la bandeja de soya"),
    lot_id: str = Form(None, description="Identificador del lote (opcional)"),
    supplier: str = Form(None, description="Nombre del proveedor (opcional)"),
):
    """
    Flujo completo:
    1. Sube la imagen a Supabase Storage → obtiene evidence_url
    2. Guarda la imagen temporalmente → llama detect_grains()
    3. summarize() → genera porcentajes
    4. generate_certificate() → veredicto + descuento + justificación
    5. Inserta la fila en `samples`
    6. Devuelve el Certificate
    """
    # --- Leer bytes de la imagen ---
    image_bytes = await image.read()
    if not image_bytes:
        raise HTTPException(status_code=400, detail="La imagen está vacía.")

    content_type = image.content_type or "image/jpeg"

    # --- 1. Subir a Supabase Storage ---
    try:
        evidence_url = db.upload_evidence(
            file_bytes=image_bytes,
            filename=image.filename or "sample.jpg",
            content_type=content_type,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Error al subir imagen a Supabase Storage: {exc}",
        )

    # --- 2. Guardar imagen temporal y detectar granos ---
    suffix = f".{image.filename.rsplit('.', 1)[-1]}" if image.filename and "." in image.filename else ".jpg"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(image_bytes)
        tmp_path = tmp.name

    try:
        detections = detect_grains(tmp_path)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Error en detect_grains: {exc}",
        )
    finally:
        os.unlink(tmp_path)

    # --- 3. Resumir detecciones ---
    breakdown = summarize(detections)

    # --- 4. Generar certificado ---
    try:
        cert = generate_certificate(
            breakdown=breakdown,
            lot_id=lot_id,
            supplier=supplier,
            evidence_image_url=evidence_url,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Error en generate_certificate: {exc}",
        )

    # --- 5. Guardar en Supabase Postgres ---
    try:
        db.insert_sample(cert)
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Error al guardar en la base de datos: {exc}",
        )

    # --- 6. Devolver certificado ---
    return cert


# --------------------------------------------------------------------------- #
#  GET /api/v1/samples
# --------------------------------------------------------------------------- #

@app.get("/api/v1/samples", tags=["muestras"])
def list_samples(limit: int = Query(50, ge=1, le=200, description="Máximo de resultados")):
    """
    Devuelve los últimos registros de `samples` ordenados por fecha descendente.
    Respuesta: { "items": [...], "total": int }
    """
    try:
        return db.get_samples(limit=limit)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Error al consultar muestras: {exc}")


# --------------------------------------------------------------------------- #
#  GET /api/v1/samples/{id}
# --------------------------------------------------------------------------- #

@app.get("/api/v1/samples/{sample_id}", tags=["muestras"])
def get_sample(sample_id: str):
    """
    Devuelve el certificado completo de una muestra por su ID.
    """
    try:
        row = db.get_sample_by_id(sample_id)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Error al consultar muestra: {exc}")

    if row is None:
        raise HTTPException(status_code=404, detail={"error": f"Muestra '{sample_id}' no encontrada."})
    return row


# --------------------------------------------------------------------------- #
#  GET /api/v1/stats/today
# --------------------------------------------------------------------------- #

@app.get("/api/v1/stats/today", tags=["estadísticas"])
def stats_today():
    """
    Estadísticas del día actual (UTC):
    { total_samples, approved, with_discount, rejected, avg_pct_danado }
    """
    try:
        return db.get_stats_today()
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Error al calcular estadísticas: {exc}")


# --------------------------------------------------------------------------- #
#  Punto de entrada para desarrollo local
# --------------------------------------------------------------------------- #

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
