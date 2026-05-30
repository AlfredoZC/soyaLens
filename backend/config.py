"""
Carga y valida las variables de entorno del backend.
Todas las variables se leen desde .env (root del proyecto).
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Busca el .env en la raíz del proyecto (soyaLens/)
_env_path = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(dotenv_path=_env_path, override=False)


def _require(var: str) -> str:
    value = os.getenv(var)
    if not value:
        raise RuntimeError(
            f"Variable de entorno requerida no encontrada: {var}\n"
            f"Asegúrate de tener un .env con {var}= en la raíz de soyaLens/"
        )
    return value


SUPABASE_URL: str = _require("SUPABASE_URL")
SUPABASE_KEY: str = _require("SUPABASE_KEY")

# Opcionales con defaults
GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
MODEL_PATH: str = os.getenv("MODEL_PATH", "ai/weights/best.pt")

# Bucket de Supabase Storage para imágenes de evidencia
STORAGE_BUCKET: str = "evidence"
