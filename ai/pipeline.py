"""
ai/pipeline.py — Interfaz pública del módulo de IA.

Expone las 3 funciones que el Backend llama (firma FIJA según PROJECT.md §6.1).
Mientras el modelo real no esté entrenado, el stub devuelve datos sintéticos
que cumplen el schema exacto definido en shared/schemas.py.

CUANDO EL MODELO ESTÉ LISTO:
    Reemplaza el cuerpo de cada función por la implementación real.
    La firma NO cambia — así el Backend no necesita modificarse.
"""

import os
import uuid
import random
from datetime import datetime, timezone
from typing import Optional

from shared.schemas import Detection, ClassBreakdown, Certificate

# --------------------------------------------------------------------------- #
#  Constante: ¿usar el modelo real o el stub?
#  Ponla en True cuando ai/weights/best.pt exista y el modelo esté listo.
# --------------------------------------------------------------------------- #
_MODEL_READY = False

# --------------------------------------------------------------------------- #
#  1. detect_grains
# --------------------------------------------------------------------------- #

def detect_grains(image_path: str) -> list[Detection]:
    """
    Recibe la ruta local a la imagen y devuelve una lista de Detection.

    Implementación real: YOLO26 + SAHI (tiling para granos densos).
    Stub: genera detecciones aleatorias realistas.
    """
    if _MODEL_READY:
        return _detect_grains_real(image_path)
    return _detect_grains_stub()


def _detect_grains_stub() -> list[Detection]:
    classes = ["sano", "sano", "sano", "sano", "partido", "inmaduro", "dañado"]
    n = random.randint(280, 340)
    return [
        Detection(
            class_name=random.choice(classes),
            confidence=round(random.uniform(0.70, 0.99), 3),
            bbox=[
                round(random.uniform(0, 500), 1),
                round(random.uniform(0, 500), 1),
                round(random.uniform(500, 1000), 1),
                round(random.uniform(500, 1000), 1),
            ],
        )
        for _ in range(n)
    ]


def _detect_grains_real(image_path: str) -> list[Detection]:
    """TODO: implementar con Ultralytics YOLO26 + SAHI."""
    raise NotImplementedError("Modelo YOLO26 aún no integrado.")


# --------------------------------------------------------------------------- #
#  2. summarize
# --------------------------------------------------------------------------- #

def summarize(detections: list[Detection]) -> ClassBreakdown:
    """
    Cuenta las detecciones por clase y calcula los porcentajes.
    Esta función NO usa IA — es matemática pura.
    """
    total = len(detections)
    if total == 0:
        return ClassBreakdown(
            total=0,
            count_sano=0, count_partido=0, count_dañado=0, count_inmaduro=0,
            pct_sano=0.0, pct_partido=0.0, pct_dañado=0.0, pct_inmaduro=0.0,
        )

    count = {"sano": 0, "partido": 0, "dañado": 0, "inmaduro": 0}
    for d in detections:
        count[d.class_name] += 1

    def pct(n: int) -> float:
        return round(n / total * 100, 2)

    return ClassBreakdown(
        total=total,
        count_sano=count["sano"],
        count_partido=count["partido"],
        count_dañado=count["dañado"],
        count_inmaduro=count["inmaduro"],
        pct_sano=pct(count["sano"]),
        pct_partido=pct(count["partido"]),
        pct_dañado=pct(count["dañado"]),
        pct_inmaduro=pct(count["inmaduro"]),
    )


# --------------------------------------------------------------------------- #
#  3. generate_certificate
# --------------------------------------------------------------------------- #

def generate_certificate(
    breakdown: ClassBreakdown,
    lot_id: Optional[str],
    supplier: Optional[str],
    evidence_image_url: str = "",
) -> Certificate:
    """
    Genera el certificado de calidad.

    Implementación real: llama a Gemini con function calling + structured output.
    Stub: aplica la norma IBNORCA NB 339 de forma determinista.
    """
    if _MODEL_READY:
        return _generate_certificate_real(breakdown, lot_id, supplier, evidence_image_url)
    return _generate_certificate_stub(breakdown, lot_id, supplier, evidence_image_url)


# --------------------------------------------------------------------------- #
#  Lógica de descuento determinista (norma IBNORCA NB 339 simplificada)
#  Esta función la llamará el agente Gemini vía function calling.
#  Se deja aquí para que el Backend también pueda usarla directamente en el stub.
# --------------------------------------------------------------------------- #

def calcular_descuento(pct_danado: float, pct_partido: float, pct_inmaduro: float) -> tuple[str, float, str]:
    """
    Devuelve: (verdict, discount_pct, justification)

    Reglas simplificadas IBNORCA NB 339:
        - pct_danado > 5%            → rechazado,     descuento 0 (no aplica)
        - 2% < pct_danado <= 5%      → con_descuento, descuento = (pct_danado - 2) * 2
        - pct_partido > 10%          → con_descuento, descuento += (pct_partido - 10) * 0.5
        - pct_danado <= 2% y resto ok → aprobado,      descuento 0
    """
    discount = 0.0
    reasons = []

    if pct_danado > 5.0:
        return (
            "rechazado",
            0.0,
            f"La muestra supera el límite máximo de 5% de grano dañado/manchado "
            f"(detectado: {pct_danado:.1f}%). No apta para comercialización. "
            f"Norma: IBNORCA NB 339.",
        )

    if pct_danado > 2.0:
        d = round((pct_danado - 2.0) * 2.0, 2)
        discount += d
        reasons.append(
            f"grano dañado/manchado {pct_danado:.1f}% (umbral 2%) → descuento {d:.1f}%"
        )

    if pct_partido > 10.0:
        d = round((pct_partido - 10.0) * 0.5, 2)
        discount += d
        reasons.append(
            f"grano partido {pct_partido:.1f}% (umbral 10%) → descuento adicional {d:.1f}%"
        )

    discount = round(min(discount, 30.0), 2)  # cap de 30%

    if discount > 0:
        verdict = "con_descuento"
        just = (
            f"La muestra presenta: {'; '.join(reasons)}. "
            f"Descuento total aplicado: {discount}%. Norma: IBNORCA NB 339."
        )
    else:
        verdict = "aprobado"
        just = (
            f"La muestra cumple todos los umbrales de la norma IBNORCA NB 339. "
            f"Grano dañado: {pct_danado:.1f}%, partido: {pct_partido:.1f}%, "
            f"inmaduro: {pct_inmaduro:.1f}%. Sin descuento."
        )

    return verdict, discount, just


def _generate_certificate_stub(
    breakdown: ClassBreakdown,
    lot_id: Optional[str],
    supplier: Optional[str],
    evidence_image_url: str,
) -> Certificate:
    verdict, discount_pct, justification = calcular_descuento(
        pct_danado=breakdown.pct_dañado,
        pct_partido=breakdown.pct_partido,
        pct_inmaduro=breakdown.pct_inmaduro,
    )
    return Certificate(
        sample_id=str(uuid.uuid4()),
        timestamp=datetime.now(timezone.utc),
        lot_id=lot_id,
        supplier=supplier,
        breakdown=breakdown,
        verdict=verdict,
        discount_pct=discount_pct,
        norm="IBNORCA NB 339",
        justification=justification,
        evidence_image_url=evidence_image_url,
    )


def _generate_certificate_real(
    breakdown: ClassBreakdown,
    lot_id: Optional[str],
    supplier: Optional[str],
    evidence_image_url: str,
) -> Certificate:
    """TODO: implementar llamada a Gemini con function calling."""
    raise NotImplementedError("Agente Gemini aún no integrado.")
