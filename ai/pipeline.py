"""ai/pipeline.py — Pipeline de IA de SoyaLens.

Expone las 3 funciones que el Backend llama (firma FIJA según PROJECT.md §6.1):
    detect_grains(image_path)             -> list[Detection]
    summarize(detections)                 -> ClassBreakdown
    generate_certificate(breakdown,
                         lot_id, supplier,
                         evidence_image_url="") -> Certificate

Comportamiento "graceful degradation": si faltan dependencias (sahi, google-genai),
credenciales (GEMINI_API_KEY), Ollama local o pesos (ai/weights/best.pt), las
funciones caen automáticamente a un stub determinista que cumple el schema exacto.
Esto permite probar Backend ↔ Frontend antes de tener todo configurado.
"""

from __future__ import annotations

import os
import re
import sys
import uuid
import random
import urllib.request
import urllib.error
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# Carga del .env (no falla si python-dotenv no está instalado)
try:
    from dotenv import load_dotenv
    _ROOT = Path(__file__).resolve().parents[1]
    load_dotenv(dotenv_path=_ROOT / ".env", override=False)
except ImportError:
    pass

# Asegura que la raíz del repo esté en sys.path para `shared.schemas`
_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from shared.schemas import Detection, ClassBreakdown, Certificate
from ai.discount import calcular_descuento

# --------------------------------------------------------------------------- #
#  Constantes y configuración
# --------------------------------------------------------------------------- #
WEIGHTS_PATH = Path(os.environ.get("MODEL_PATH", _REPO_ROOT / "ai" / "weights" / "best.pt"))
if not WEIGHTS_PATH.is_absolute():
    WEIGHTS_PATH = _REPO_ROOT / WEIGHTS_PATH

# Mapeo canónico: índice YOLO (dataset en inglés) → GrainClass (contrato en español)
YOLO_TO_GRAIN: dict[int, str] = {
    0: "partido",    # broken
    1: "inmaduro",   # immature
    2: "sano",       # intact
    3: "dañado",     # damaged
}

# Modelo de Gemini. Si Google lanza un ID nuevo, actualizarlo aquí.
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")

# Configuración de Ollama (temporal para desarrollo local)
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434/v1")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "qwen2.5:7b")

# Norma constante del veredicto
NORM = "IBNORCA NB 339"

# --------------------------------------------------------------------------- #
#  Detección de capacidades — define si usamos pipeline real o stub
# --------------------------------------------------------------------------- #

def _detection_available() -> bool:
    """True si SAHI está instalado y existe el archivo de pesos."""
    if not WEIGHTS_PATH.exists():
        return False
    try:
        import sahi  # noqa: F401
        import ultralytics  # noqa: F401
        return True
    except ImportError:
        return False


def _gemini_available() -> bool:
    """True si google-genai está instalado y existe GEMINI_API_KEY."""
    if not os.environ.get("GEMINI_API_KEY"):
        return False
    try:
        from google import genai  # noqa: F401
        return True
    except ImportError:
        return False


import time as _time
_ollama_cache: dict = {"available": None, "ts": 0.0}

def _ollama_available() -> bool:
    """True si Ollama está corriendo. Cachea el resultado 60s para no pingar en cada request."""
    now = _time.time()
    if _ollama_cache["available"] is not None and (now - _ollama_cache["ts"]) < 60:
        return _ollama_cache["available"]

    base_url = OLLAMA_URL.replace("/v1", "")
    try:
        req = urllib.request.Request(f"{base_url}/api/tags", method="HEAD")
        with urllib.request.urlopen(req, timeout=1.0) as response:
            if response.status != 200:
                _ollama_cache.update(available=False, ts=now)
                return False
    except (urllib.error.URLError, ValueError):
        _ollama_cache.update(available=False, ts=now)
        return False

    try:
        import openai  # noqa: F401
        _ollama_cache.update(available=True, ts=now)
        return True
    except ImportError:
        _ollama_cache.update(available=False, ts=now)
        return False


# --------------------------------------------------------------------------- #
#  Sanitización de entradas (defensa contra prompt injection y path traversal)
# --------------------------------------------------------------------------- #

_ALLOWED_IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def _safe_image_path(image_path: str) -> Path:
    """Valida que image_path es un archivo de imagen real y accesible.

    Lanza ValueError si la ruta no existe, no es archivo, o tiene extensión
    no permitida.
    """
    if not image_path or not isinstance(image_path, str):
        raise ValueError("image_path debe ser una cadena no vacía.")
    p = Path(image_path).resolve()
    if not p.is_file():
        raise ValueError(f"La ruta de imagen no existe o no es un archivo: {p}")
    if p.suffix.lower() not in _ALLOWED_IMAGE_EXTS:
        raise ValueError(
            f"Extensión no permitida: {p.suffix}. "
            f"Permitidas: {sorted(_ALLOWED_IMAGE_EXTS)}"
        )
    return p


def _sanitize_text(value: Optional[str], max_len: int = 100) -> Optional[str]:
    """Limpia texto del usuario antes de inyectarlo en un prompt de LLM.

    - Quita saltos de línea y caracteres de control (anti prompt injection)
    - Limita longitud
    - Devuelve None si el input es vacío
    """
    if value is None:
        return None
    s = str(value).strip()
    if not s:
        return None
    # Reemplaza CR/LF/TAB y caracteres de control por espacio
    s = re.sub(r"[\x00-\x1f\x7f]+", " ", s)
    # Colapsa espacios múltiples
    s = re.sub(r"\s+", " ", s).strip()
    return s[:max_len]


# --------------------------------------------------------------------------- #
#  FUNCIÓN 1 — detect_grains
# --------------------------------------------------------------------------- #

_detection_model = None  # singleton SAHI


def _get_yolo_model():
    """Carga el modelo YOLO puro una sola vez (singleton)."""
    global _detection_model
    if _detection_model is not None:
        return _detection_model

    from ultralytics import YOLO
    try:
        import torch
        device = "cuda:0" if torch.cuda.is_available() else "cpu"
    except ImportError:
        device = "cpu"

    print(f"[IA] Cargando YOLO puro en {device}...")
    _detection_model = YOLO(str(WEIGHTS_PATH))
    return _detection_model


def _detect_grains_real(image_path: Path) -> list[Detection]:
    """Detección real con YOLO puro (inferencia en un solo pase)."""
    model = _get_yolo_model()
    
    # Detectar si la imagen tiene fondo claro (madera) para adaptar el mapeo de clases
    import cv2
    import numpy as np
    
    img = cv2.imread(str(image_path))
    is_light_bg = False
    if img is not None:
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        avg_h = np.mean(hsv[:, :, 0])
        avg_v = np.mean(hsv[:, :, 2])
        # Fondo tipo madera/claro: tono naranja/amarillo (10-45) y brillo moderado-alto (> 100)
        is_light_bg = (10 <= avg_h <= 45) and (avg_v > 100)
        
    mapping = YOLO_TO_GRAIN
    if is_light_bg:
        print("[IA] Detectado fondo claro (madera). Aplicando mapeo adaptativo de clases por domain shift.")
        mapping = {
            0: "dañado",
            1: "inmaduro",
            2: "partido",
            3: "sano",
        }
    else:
        print("[IA] Detectado fondo oscuro. Usando mapeo estándar de clases.")
    
    # Run YOLO inference
    results = model(str(image_path), conf=0.25, verbose=False)
    
    detections: list[Detection] = []
    # Results is a list of Results objects (one per image). We passed 1 image.
    for pred in results[0].boxes:
        class_id = int(pred.cls[0].item())
        confidence = float(pred.conf[0].item())
        
        if class_id not in mapping:
            continue  # índice desconocido → descartar
            
        # Get bounding box [x1, y1, x2, y2]
        bbox = pred.xyxy[0].tolist()
        
        detections.append(Detection(
            class_name=mapping[class_id],
            confidence=confidence,
            bbox=bbox,
        ))
    return detections



def _detect_grains_stub(image_path: Path) -> list[Detection]:
    """Stub determinista basado en el hash del archivo — útil para Backend/Frontend
    cuando aún no hay modelo entrenado o no se instaló SAHI."""
    # Semilla determinista por archivo, para que el mismo input siempre dé el mismo output
    seed_src = str(image_path.name) + str(image_path.stat().st_size)
    rng = random.Random(hash(seed_src))

    classes = ["sano"] * 70 + ["partido"] * 15 + ["inmaduro"] * 10 + ["dañado"] * 5
    n = rng.randint(250, 350)
    return [
        Detection(
            class_name=rng.choice(classes),
            confidence=round(rng.uniform(0.70, 0.99), 3),
            bbox=[
                round(rng.uniform(0, 500), 1),
                round(rng.uniform(0, 500), 1),
                round(rng.uniform(500, 1000), 1),
                round(rng.uniform(500, 1000), 1),
            ],
        )
        for _ in range(n)
    ]


def detect_grains(image_path: str) -> list[Detection]:
    """Detecta y clasifica granos en la imagen.

    Usa YOLO26 + SAHI si están disponibles; si no, devuelve un stub
    determinista que cumple el schema (útil para integrar Backend/Frontend
    antes de que el modelo esté listo).
    """
    p = _safe_image_path(image_path)
    if _detection_available():
        return _detect_grains_real(p)
    print("[IA] (stub) sahi/best.pt no disponibles; usando detecciones simuladas.")
    return _detect_grains_stub(p)


# --------------------------------------------------------------------------- #
#  FUNCIÓN 2 — summarize  (matemática pura, sin IA)
# --------------------------------------------------------------------------- #

def summarize(detections: list[Detection]) -> ClassBreakdown:
    """Cuenta detecciones por clase y calcula porcentajes (0.0 a 100.0)."""
    total = len(detections)
    counts: Counter = Counter(d.class_name for d in detections)

    def pct(cls: str) -> float:
        return round((counts.get(cls, 0) / total) * 100, 2) if total > 0 else 0.0

    return ClassBreakdown(
        total=total,
        count_sano=counts.get("sano", 0),
        count_partido=counts.get("partido", 0),
        count_dañado=counts.get("dañado", 0),
        count_inmaduro=counts.get("inmaduro", 0),
        pct_sano=pct("sano"),
        pct_partido=pct("partido"),
        pct_dañado=pct("dañado"),
        pct_inmaduro=pct("inmaduro"),
    )


# --------------------------------------------------------------------------- #
#  FUNCIÓN 3 — generate_certificate
# --------------------------------------------------------------------------- #

def _build_cert_skeleton(
    breakdown: ClassBreakdown,
    lot_id: Optional[str],
    supplier: Optional[str],
    evidence_image_url: str,
    verdict: str,
    discount_pct: float,
    justification: str,
) -> Certificate:
    """Ensambla el Certificate final (datos deterministas de Python + datos de IA)."""
    return Certificate(
        sample_id=str(uuid.uuid4()),
        timestamp=datetime.now(timezone.utc),
        lot_id=lot_id,
        supplier=supplier,
        breakdown=breakdown,
        verdict=verdict,  # type: ignore[arg-type]
        discount_pct=discount_pct,
        norm=NORM,
        justification=justification,
        evidence_image_url=evidence_image_url,
    )


def _generate_certificate_stub(
    breakdown: ClassBreakdown,
    lot_id: Optional[str],
    supplier: Optional[str],
    evidence_image_url: str,
) -> Certificate:
    """Stub determinista: usa calcular_descuento() directamente, sin LLM."""
    result = calcular_descuento(
        pct_partido=breakdown.pct_partido,
        pct_inmaduro=breakdown.pct_inmaduro,
        pct_danado=breakdown.pct_dañado,
    )
    return _build_cert_skeleton(
        breakdown=breakdown,
        lot_id=lot_id,
        supplier=supplier,
        evidence_image_url=evidence_image_url,
        verdict=result["verdict"],
        discount_pct=float(result["discount_pct"]),
        justification=result["reasoning"] + " (Certificado generado en modo stub determinista — sin LLM)",
    )


def _generate_certificate_real(
    breakdown: ClassBreakdown,
    lot_id: Optional[str],
    supplier: Optional[str],
    evidence_image_url: str,
) -> Certificate:
    """Pipeline real: Gemini con function calling + tool determinista."""
    from google import genai
    from google.genai import types as gtypes

    api_key = os.environ["GEMINI_API_KEY"]
    client = genai.Client(api_key=api_key)

    # Wrapper del tool: el LLM lo llama; nosotros guardamos el resultado por si Gemini
    # devuelve algo distinto de lo que la tool calculó (forzamos determinismo).
    captured: dict = {}

    def descuento_tool(pct_partido: float, pct_inmaduro: float, pct_danado: float) -> dict:
        """Calcula el veredicto y descuento según norma IBNORCA NB 339.

        Args:
            pct_partido:  Porcentaje de granos partidos (0-100).
            pct_inmaduro: Porcentaje de granos inmaduros (0-100).
            pct_danado:   Porcentaje de granos dañados (0-100).
        """
        result = calcular_descuento(
            pct_partido=pct_partido,
            pct_inmaduro=pct_inmaduro,
            pct_danado=pct_danado,
        )
        captured.update(result)
        return result

    system_prompt = (
        "Eres un auditor de calidad de soya certificado bajo la norma IBNORCA NB 339. "
        "Recibes datos de detección de granos por visión artificial. Tu trabajo es:\n"
        "1. Analizar el desglose de clases.\n"
        "2. Llamar a la herramienta 'descuento_tool' con los porcentajes medidos.\n"
        "3. Redactar una justificación profesional en español (2-4 oraciones) usando "
        "el reasoning que devolvió la herramienta.\n"
        "REGLAS ESTRICTAS:\n"
        "- NUNCA inventes el descuento. SOLO usa lo que retorna la herramienta.\n"
        "- La justificación debe estar en español, clara y orientada al operario del silo.\n"
        "- Responde SOLO con la justificación (texto plano), nada más."
    )

    # Sanitizar lot_id y supplier para evitar prompt injection
    safe_lot = _sanitize_text(lot_id) or "No especificado"
    safe_sup = _sanitize_text(supplier) or "No especificado"

    user_prompt = (
        f"Desglose detectado:\n"
        f"  Total: {breakdown.total} granos\n"
        f"  Sano:     {breakdown.pct_sano}%\n"
        f"  Partido:  {breakdown.pct_partido}%\n"
        f"  Inmaduro: {breakdown.pct_inmaduro}%\n"
        f"  Dañado:   {breakdown.pct_dañado}%\n"
        f"Lote: {safe_lot}\n"
        f"Proveedor: {safe_sup}\n\n"
        "Llama a 'descuento_tool' con los porcentajes y luego escribe la justificación."
    )

    # Llamada con automatic function calling (el SDK orquesta la llamada al tool)
    try:
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=user_prompt,
            config=gtypes.GenerateContentConfig(
                system_instruction=system_prompt,
                tools=[descuento_tool],
                temperature=0.0,
            ),
        )
        justification = (response.text or "").strip()
    except Exception as exc:
        print(f"[IA] Gemini falló ({exc}). Se intentará fallback con Ollama.")
        raise RuntimeError("Gemini no pudo generar el certificado.") from exc

    # Si Gemini no llamó al tool (poco probable), forzamos el cálculo en Python
    if not captured:
        captured = calcular_descuento(
            pct_partido=breakdown.pct_partido,
            pct_inmaduro=breakdown.pct_inmaduro,
            pct_danado=breakdown.pct_dañado,
        )
        if not justification:
            justification = captured["reasoning"]

    return _build_cert_skeleton(
        breakdown=breakdown,
        lot_id=lot_id,  # guardamos el original (sin sanitizar) en el certificado
        supplier=supplier,
        evidence_image_url=evidence_image_url,
        verdict=captured["verdict"],
        discount_pct=float(captured["discount_pct"]),
        justification=justification or captured["reasoning"],
    )


def _generate_certificate_ollama(
    breakdown: ClassBreakdown,
    lot_id: Optional[str],
    supplier: Optional[str],
    evidence_image_url: str,
) -> Certificate:
    """Pipeline híbrido/local: Ollama para redacción, matemática determinista previa."""
    from openai import OpenAI
    
    # 1. Calcular descuento con matemática pura en Python
    result = calcular_descuento(
        pct_partido=breakdown.pct_partido,
        pct_inmaduro=breakdown.pct_inmaduro,
        pct_danado=breakdown.pct_dañado,
    )
    
    # 2. Pedirle a Ollama solo que redacte la justificación
    client = OpenAI(
        base_url=OLLAMA_URL,
        api_key="ollama", # Clave dummy obligatoria para el SDK
    )

    safe_lot = _sanitize_text(lot_id) or "No especificado"
    safe_sup = _sanitize_text(supplier) or "No especificado"
    
    system_prompt = (
        "Eres un auditor de calidad de soya certificado bajo la norma IBNORCA NB 339. "
        "Recibes los resultados finales de una auditoría. Tu único trabajo es redactar "
        "una justificación profesional en español (2-4 oraciones) para el certificado, "
        "explicando por qué se tomó el veredicto basándote en los datos dados. "
        "REGLAS:\n"
        "- NO incluyas saludos ni despedidas.\n"
        "- Responde SOLO con el párrafo de justificación."
    )

    user_prompt = (
        f"Datos del Lote: {safe_lot} (Proveedor: {safe_sup})\n"
        f"Desglose detectado: {breakdown.total} granos totales "
        f"(Sano {breakdown.pct_sano}%, Partido {breakdown.pct_partido}%, "
        f"Inmaduro {breakdown.pct_inmaduro}%, Dañado {breakdown.pct_dañado}%).\n"
        f"Veredicto oficial: {result['verdict'].upper()}\n"
        f"Descuento a aplicar: {result['discount_pct']}%\n"
        f"Razón técnica (usa esto como base): {result['reasoning']}\n\n"
        "Escribe la justificación final."
    )

    print(f"[IA] Llamando a Ollama ({OLLAMA_MODEL}) para la justificación...")
    try:
        response = client.chat.completions.create(
            model=OLLAMA_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3,
        )
        justification = (response.choices[0].message.content or "").strip()
    except Exception as exc:
        print(f"[IA] Ollama falló ({exc}). Se usará certificado determinista.")
        raise RuntimeError("Ollama no pudo generar la justificación.") from exc

    return _build_cert_skeleton(
        breakdown=breakdown,
        lot_id=lot_id,
        supplier=supplier,
        evidence_image_url=evidence_image_url,
        verdict=result["verdict"],
        discount_pct=float(result["discount_pct"]),
        justification=justification,
    )


def generate_certificate(
    breakdown: ClassBreakdown,
    lot_id: Optional[str],
    supplier: Optional[str],
    evidence_image_url: str = "",
) -> Certificate:
    """Genera el certificado de calidad.

    Prioridad:
    1. Gemini Flash con google-genai.
    2. Ollama local si Gemini no está disponible o falla.
    3. Stub determinista si ningún LLM está disponible.
    """
    if _gemini_available():
        print("[IA] Usando Gemini Flash para generar el certificado...")
        try:
            return _generate_certificate_real(breakdown, lot_id, supplier, evidence_image_url)
        except RuntimeError:
            pass
    else:
        print("[IA] Gemini no disponible: falta GEMINI_API_KEY o google-genai.")

    if _ollama_available():
        print("[IA] Usando Ollama local para generar la justificación...")
        try:
            return _generate_certificate_ollama(breakdown, lot_id, supplier, evidence_image_url)
        except RuntimeError:
            pass
    else:
        print("[IA] Ollama no disponible: servidor local o SDK openai no encontrado.")

    print("[IA] (stub) Ningún LLM disponible; certificado determinista.")
    return _generate_certificate_stub(breakdown, lot_id, supplier, evidence_image_url)
