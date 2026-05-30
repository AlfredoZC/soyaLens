from pydantic import BaseModel, Field
from typing import Literal, Optional
from datetime import datetime

# Las 4 clases de grano (NO agregar más sin acuerdo de equipo).
# Traducción de las clases del dataset (ai/dataset/data.yaml):
#   broken→partido, immature→inmaduro, intact→sano, damaged→dañado
GrainClass = Literal["sano", "partido", "dañado", "inmaduro"]

class Detection(BaseModel):
    """Representa un único grano detectado por YOLO."""
    class_name: GrainClass
    confidence: float
    bbox: list[float]  # [x1, y1, x2, y2]

class ClassBreakdown(BaseModel):
    """Resumen estadístico de todos los granos detectados en la muestra."""
    total: int
    count_sano: int
    count_partido: int
    count_dañado: int
    count_inmaduro: int
    pct_sano: float
    pct_partido: float
    pct_dañado: float
    pct_inmaduro: float

class Certificate(BaseModel):
    """El certificado oficial generado por la IA (Gemini) que se guarda en BD."""
    sample_id: str
    timestamp: datetime
    lot_id: Optional[str] = None
    supplier: Optional[str] = None
    breakdown: ClassBreakdown
    verdict: Literal["aprobado", "con_descuento", "rechazado"]
    discount_pct: float            # De 0.0 a 100.0
    norm: str                      # ej. "IBNORCA NB 339"
    justification: str             # Explicación del agente en español
    evidence_image_url: str        # URL de la imagen en Supabase Storage
