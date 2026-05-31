"""
Módulo de acceso a datos — Supabase (Postgres + Storage).
Todas las operaciones de BD pasan por aquí; el main.py NO importa supabase directamente.
"""
import uuid
import mimetypes
from datetime import datetime, timezone
from typing import Optional

from supabase import create_client, Client

from backend.config import SUPABASE_URL, SUPABASE_KEY, STORAGE_BUCKET
from shared.schemas import Certificate, ClassBreakdown

# --------------------------------------------------------------------------- #
#  Cliente singleton
# --------------------------------------------------------------------------- #
_client: Optional[Client] = None


def get_client() -> Client:
    global _client
    if _client is None:
        _client = create_client(SUPABASE_URL, SUPABASE_KEY)
    return _client


# --------------------------------------------------------------------------- #
#  Storage — subir imagen de evidencia
# --------------------------------------------------------------------------- #

def upload_evidence(file_bytes: bytes, filename: str, content_type: str) -> str:
    """
    Sube la imagen al bucket 'evidence' de Supabase Storage.
    Devuelve la URL pública del archivo.
    """
    client = get_client()
    # Genera un nombre único para evitar colisiones
    ext = filename.rsplit(".", 1)[-1] if "." in filename else "jpg"
    unique_name = f"{uuid.uuid4()}.{ext}"

    client.storage.from_(STORAGE_BUCKET).upload(
        path=unique_name,
        file=file_bytes,
        file_options={"content-type": content_type, "upsert": "false"},
    )

    # URL pública (el bucket debe ser público para la demo)
    public_url: str = (
        client.storage.from_(STORAGE_BUCKET).get_public_url(unique_name)
    )
    return public_url


# --------------------------------------------------------------------------- #
#  Postgres — insertar y consultar tabla `samples`
# --------------------------------------------------------------------------- #

def insert_sample(cert: Certificate) -> str:
    """
    Inserta un certificado en la tabla `samples`.
    Devuelve el ID (uuid) de la fila creada.
    """
    client = get_client()
    row = {
        "id": cert.sample_id,
        "lot_id": cert.lot_id,
        "supplier": cert.supplier,
        "evidence_url": cert.evidence_image_url,
        "total_grains": cert.breakdown.total,
        "pct_sano": cert.breakdown.pct_sano,
        "pct_partido": cert.breakdown.pct_partido,
        "pct_inmaduro": cert.breakdown.pct_inmaduro,
        "pct_dañado": cert.breakdown.pct_dañado,  # columna con ñ en Supabase
        "verdict": cert.verdict,
        "discount_pct": cert.discount_pct,
        "norm": cert.norm,
        "justification": cert.justification,
    }
    response = client.table("samples").insert(row).execute()
    return response.data[0]["id"]


def get_samples(limit: int = 50) -> dict:
    """
    Devuelve los últimos `limit` registros de `samples` ordenados por fecha desc.
    """
    client = get_client()
    response = (
        client.table("samples")
        .select(
            "id, created_at, lot_id, supplier, verdict, pct_dañado, discount_pct, evidence_url"
        )
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    return {"items": response.data or [], "total": len(response.data or [])}


def get_sample_by_id(sample_id: str) -> Optional[dict]:
    """
    Devuelve el registro completo de `samples` para el ID dado, o None si no existe.
    """
    client = get_client()
    response = (
        client.table("samples")
        .select("*")
        .eq("id", sample_id)
        .limit(1)
        .execute()
    )
    if not response.data:
        return None
    return response.data[0]


def get_stats_today() -> dict:
    """
    Calcula estadísticas del día actual (UTC) desde la tabla `samples`.
    """
    client = get_client()
    today_start = datetime.now(timezone.utc).replace(
        hour=0, minute=0, second=0, microsecond=0
    ).isoformat()

    response = (
        client.table("samples")
        .select("verdict, pct_dañado")
        .gte("created_at", today_start)
        .execute()
    )
    rows = response.data or []

    total = len(rows)
    approved = sum(1 for r in rows if r.get("verdict") == "aprobado")
    with_discount = sum(1 for r in rows if r.get("verdict") == "con_descuento")
    rejected = sum(1 for r in rows if r.get("verdict") == "rechazado")
    avg_pct_danado = (
        sum(float(r.get("pct_dañado") or 0) for r in rows) / total if total > 0 else 0.0
    )

    return {
        "total_samples": total,
        "approved": approved,
        "with_discount": with_discount,
        "rejected": rejected,
        "avg_pct_danado": round(avg_pct_danado, 2),
    }
