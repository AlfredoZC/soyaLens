"""
tests/test_backend.py — Smoke tests del backend SoyaLens.

Verifica:
  1. GET /health → 200, { "status": "ok" }
  2. POST /api/v1/analyze → 200, respuesta cumple schema Certificate
  3. GET /api/v1/samples → 200, tiene claves "items" y "total"
  4. GET /api/v1/stats/today → 200, tiene claves esperadas

Para correr:
    cd soyaLens
    ..\\envBwaiBackend\\Scripts\\python.exe -m pytest tests/test_backend.py -v
"""

import sys
import io
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Asegura que la raíz del proyecto esté en el path
_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

# --- Mockear Supabase antes de importar el backend ---
# Evita que los tests necesiten credenciales reales de Supabase.
import unittest.mock as mock

_FAKE_CERT = {
    "sample_id": "test-001",
    "timestamp": "2026-05-31T09:00:00+00:00",
    "lot_id": "L-TEST",
    "supplier": "Test Supplier",
    "breakdown": {
        "total": 300,
        "count_sano": 280,
        "count_partido": 10,
        "count_dañado": 5,
        "count_inmaduro": 5,
        "pct_sano": 93.33,
        "pct_partido": 3.33,
        "pct_dañado": 1.67,
        "pct_inmaduro": 1.67,
    },
    "verdict": "aprobado",
    "discount_pct": 0.0,
    "norm": "IBNORCA NB 339",
    "justification": "La muestra cumple todos los umbrales.",
    "evidence_image_url": "https://example.com/evidence/test.jpg",
}


@pytest.fixture(scope="module")
def client():
    """TestClient con Supabase mockeado."""
    with (
        mock.patch("backend.db.upload_evidence", return_value="https://example.com/evidence/test.jpg"),
        mock.patch("backend.db.insert_sample", return_value="test-001"),
        mock.patch("backend.db.get_samples", return_value={"items": [_FAKE_CERT], "total": 1}),
        mock.patch("backend.db.get_sample_by_id", return_value=_FAKE_CERT),
        mock.patch("backend.db.get_stats_today", return_value={
            "total_samples": 1, "approved": 1, "with_discount": 0,
            "rejected": 0, "avg_pct_danado": 1.67,
        }),
    ):
        from backend.main import app
        yield TestClient(app)


# --------------------------------------------------------------------------- #
#  Tests
# --------------------------------------------------------------------------- #

def test_health(client):
    """GET /health debe devolver 200 con status ok."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_analyze_returns_certificate(client):
    """POST /api/v1/analyze debe devolver un Certificate válido."""
    # Imagen mínima válida (1x1 px PNG)
    fake_png = (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
        b"\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00"
        b"\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18"
        b"\xd8N\x00\x00\x00\x00IEND\xaeB`\x82"
    )
    response = client.post(
        "/api/v1/analyze",
        files={"image": ("test.png", io.BytesIO(fake_png), "image/png")},
        data={"lot_id": "L-TEST", "supplier": "Test Supplier"},
    )
    assert response.status_code == 200, response.text
    data = response.json()

    # Verifica campos requeridos del schema Certificate
    required_fields = [
        "sample_id", "timestamp", "breakdown", "verdict",
        "discount_pct", "norm", "justification", "evidence_image_url",
    ]
    for field in required_fields:
        assert field in data, f"Campo faltante: {field}"

    # Verifica que breakdown tiene los porcentajes
    breakdown = data["breakdown"]
    assert "total" in breakdown
    assert "pct_sano" in breakdown
    assert "pct_dañado" in breakdown


def test_list_samples(client):
    """GET /api/v1/samples debe devolver items y total."""
    response = client.get("/api/v1/samples")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert isinstance(data["items"], list)


def test_stats_today(client):
    """GET /api/v1/stats/today debe devolver las 5 métricas."""
    response = client.get("/api/v1/stats/today")
    assert response.status_code == 200
    data = response.json()
    expected_keys = ["total_samples", "approved", "with_discount", "rejected", "avg_pct_danado"]
    for key in expected_keys:
        assert key in data, f"Clave faltante en stats: {key}"


def test_sample_not_found(client):
    """GET /api/v1/samples/{id} con ID inexistente debe devolver 404."""
    with mock.patch("backend.db.get_sample_by_id", return_value=None):
        response = client.get("/api/v1/samples/no-existe-este-id")
    assert response.status_code == 404
