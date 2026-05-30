def calcular_descuento(
    norm: str,
    pct_partido: float,
    pct_inmaduro: float,
    pct_danado: float,
) -> dict:
    """
    Calcula el descuento según la norma boliviana (simplificada para el MVP).
    
    Retorna un diccionario con:
        - verdict: "aprobado", "con_descuento" o "rechazado"
        - discount_pct: Porcentaje de descuento aplicado (0.0 a 100.0)
        - reasoning: Explicación textual que usará Gemini
    """
    total_defectos = pct_partido + pct_inmaduro + pct_danado
    
    if pct_danado <= 2.0 and total_defectos <= 5.0:
        return {
            "verdict": "aprobado",
            "discount_pct": 0.0,
            "reasoning": (
                f"Defectos totales ({total_defectos:.1f}%) dentro del umbral de 5%. "
                f"Grano dañado ({pct_danado:.1f}%) dentro del umbral de 2%. "
                "Muestra clasificada como Grado 1 (Aprobada)."
            ),
        }
    elif pct_danado <= 5.0 and total_defectos <= 15.0:
        exceso = total_defectos - 5.0
        discount = round(exceso * 0.5, 2)
        return {
            "verdict": "con_descuento",
            "discount_pct": discount,
            "reasoning": (
                f"Defectos totales ({total_defectos:.1f}%) superan el umbral de 5%. "
                f"Exceso de {exceso:.1f}%, se aplica descuento de {discount}%. "
                f"Grano dañado ({pct_danado:.1f}%) dentro del umbral de 5%. "
                "Muestra clasificada como Grado 2 (Con descuento)."
            ),
        }
    else:
        discount = round(total_defectos * 0.8, 2)
        return {
            "verdict": "rechazado",
            "discount_pct": min(discount, 100.0),
            "reasoning": (
                f"Defectos totales ({total_defectos:.1f}%) superan el umbral de 15% "
                f"o grano dañado ({pct_danado:.1f}%) supera el 5%. "
                f"Descuento calculado del {discount}%. Muestra clasificada como Grado 3 (Rechazada)."
            ),
        }
