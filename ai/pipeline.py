import sys
import os
import uuid
from datetime import datetime
from collections import Counter
from dotenv import load_dotenv

from google import genai
from google.genai.types import GenerateContentConfig
from sahi import AutoDetectionModel
from sahi.predict import get_sliced_prediction
import torch

try:
    from langfuse.decorators import observe
except ImportError:
    # Si falla, definimos un decorador dummy para que el código siga funcionando
    def observe(*args, **kwargs):
        def decorator(func):
            return func
        return decorator

# Asegurar que se puede importar shared
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.schemas import Detection, ClassBreakdown, Certificate
from ai.discount import calcular_descuento

load_dotenv()

# Rutas
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WEIGHTS_PATH = os.path.join(BASE_DIR, "ai", "weights", "best.pt")

# Mapeo de índices de YOLO (inglés) a GrainClass (español)
YOLO_TO_GRAIN: dict[int, str] = {
    0: "partido",
    1: "inmaduro",
    2: "sano",
    3: "dañado",
}

# Singleton para cargar el modelo de visión
_detection_model: AutoDetectionModel | None = None

def _get_model() -> AutoDetectionModel:
    global _detection_model
    if _detection_model is None:
        device = "cuda:0" if torch.cuda.is_available() else "cpu"
        print(f"[IA] Cargando modelo YOLO26 en {device} con SAHI...")
        _detection_model = AutoDetectionModel.from_pretrained(
            model_type="ultralytics",
            model_path=str(WEIGHTS_PATH),
            confidence_threshold=0.25,
            device=device,
        )
    return _detection_model

def detect_grains(image_path: str) -> list[Detection]:
    """Escanea la imagen con YOLO26 + SAHI (tiling) para encontrar granos."""
    model = _get_model()
    print(f"[IA] Escaneando {image_path}...")
    
    result = get_sliced_prediction(
        image_path,
        model,
        slice_height=640,
        slice_width=640,
        overlap_height_ratio=0.2,
        overlap_width_ratio=0.2,
    )
    
    detections = []
    for pred in result.object_prediction_list:
        bbox = pred.bbox.to_xyxy()  # [x1, y1, x2, y2]
        class_id = pred.category.id
        
        # Mapeamos el ID al nombre en español
        class_name_es = YOLO_TO_GRAIN.get(class_id, "sano")
        
        detections.append(Detection(
            class_name=class_name_es,  # type: ignore
            confidence=pred.score.value,
            bbox=bbox,
        ))
        
    return detections

def summarize(detections: list[Detection]) -> ClassBreakdown:
    """Calcula totales y porcentajes de las detecciones."""
    total = len(detections)
    counts = Counter(d.class_name for d in detections)

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

@observe(name="generate_certificate")
def generate_certificate(
    breakdown: ClassBreakdown,
    lot_id: str | None,
    supplier: str | None,
) -> Certificate:
    """
    Usa Gemini 3 Flash para redactar el certificado.
    Llama a calcular_descuento() para la matemática determinista.
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY no está configurada en .env")
        
    client = genai.Client(api_key=api_key)

    system_prompt = """
    Eres un auditor de calidad de soya certificado bajo la norma IBNORCA NB 339.
    Se te entregan datos de detección de granos por visión artificial.
    Tu trabajo:
    1. Analizar el desglose de clases (ClassBreakdown).
    2. Llamar a la herramienta 'calcular_descuento' con los porcentajes medidos para obtener el veredicto y el descuento oficial.
    3. Usar los resultados de la herramienta para generar el certificado estructurado.
    4. Escribir una justificación clara y profesional en español en el campo `justification`.
    
    REGLAS:
    - NUNCA inventes el porcentaje de descuento o el veredicto. Usa SOLO lo que retorne la herramienta 'calcular_descuento'.
    - La norma SIEMPRE es "IBNORCA NB 339".
    - El campo evidence_image_url déjalo vacío ("").
    - Los campos timestamp y sample_id pon cualquier valor (se sobreescriben en Python).
    """

    user_prompt = f"""
    Desglose:
    Total: {breakdown.total} granos
    - Sano: {breakdown.pct_sano}%
    - Partido: {breakdown.pct_partido}%
    - Dañado: {breakdown.pct_dañado}%
    - Inmaduro: {breakdown.pct_inmaduro}%
    
    Lote: {lot_id or "N/A"}
    Proveedor: {supplier or "N/A"}
    
    Por favor, llama a la herramienta calcular_descuento con norm="IBNORCA NB 339" y los porcentajes.
    Luego genera el certificado final.
    """

    print("[IA] Llamando a Gemini 3.5 Flash...")
    response = client.models.generate_content(
        model="gemini-3.5-flash",
        contents=user_prompt,
        config=GenerateContentConfig(
            system_instruction=system_prompt,
            tools=[calcular_descuento],
            response_mime_type="application/json",
            response_schema=Certificate,
            temperature=0.0,
        ),
    )

    cert: Certificate = response.parsed  # type: ignore

    # Sobreescribir campos fijos para asegurar determinismo
    cert.sample_id = str(uuid.uuid4())
    cert.timestamp = datetime.now()
    cert.evidence_image_url = ""
    cert.lot_id = lot_id
    cert.supplier = supplier
    cert.breakdown = breakdown

    print(f"[IA] Certificado generado. Veredicto: {cert.verdict}")
    return cert
