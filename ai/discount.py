"""Lógica determinista de descuento según norma IBNORCA NB 339.

El LLM (Gemini) llama a esta función como tool — NO inventa el descuento.
También se usa directamente en el stub de `generate_certificate` cuando no
hay GEMINI_API_KEY configurada.
"""

from __future__ import annotations


def calcular_descuento(
    pct_partido: float,
    pct_inmaduro: float,
    pct_danado: float,
) -> dict:
    """Calcula veredicto y descuento de soya según norma IBNORCA NB 339 (simplificada).

    Args:
        pct_partido:  Porcentaje de granos partidos detectados (0-100).
        pct_inmaduro: Porcentaje de granos inmaduros detectados (0-100).
        pct_danado:   Porcentaje de granos dañados detectados (0-100).

    Returns:
        Diccionario con:
          - verdict: "aprobado" | "con_descuento" | "rechazado"
          - discount_pct: float (0.0 - 100.0)
          - reasoning: str — explicación textual
    """
    total_defectos = pct_partido + pct_inmaduro + pct_danado

    # Grado 1 — aprobado: defectos totales ≤ 5% y dañado ≤ 2%
    if pct_danado <= 2.0 and total_defectos <= 5.0:
        return {
            "verdict": "aprobado",
            "discount_pct": 0.0,
            "reasoning": (
                f"Defectos totales ({total_defectos:.1f}%) dentro del umbral de 5%. "
                f"Grano dañado ({pct_danado:.1f}%) dentro del umbral de 2%. "
                "Muestra clasificada como Grado 1 (aprobada sin descuento)."
            ),
        }

    # Grado 2 — con descuento: defectos ≤ 15% y dañado ≤ 5%
    if pct_danado <= 5.0 and total_defectos <= 15.0:
        exceso = total_defectos - 5.0
        discount = round(exceso * 0.5, 2)  # 0.5% por cada 1% de exceso
        return {
            "verdict": "con_descuento",
            "discount_pct": discount,
            "reasoning": (
                f"Defectos totales ({total_defectos:.1f}%) superan el umbral de 5%. "
                f"Exceso de {exceso:.1f}%, descuento aplicado: {discount}%. "
                f"Grano dañado ({pct_danado:.1f}%) dentro del umbral de 5%. "
                "Muestra clasificada como Grado 2."
            ),
        }

    # Grado 3 — rechazado: defectos > 15% o dañado > 5%
    discount = round(min(total_defectos * 0.8, 100.0), 2)
    return {
        "verdict": "rechazado",
        "discount_pct": discount,
        "reasoning": (
            f"Defectos totales ({total_defectos:.1f}%) superan el umbral de 15% "
            f"o grano dañado ({pct_danado:.1f}%) supera el 5%. "
            f"Descuento de {discount}%. Muestra clasificada como Grado 3 (rechazada)."
        ),
    }
