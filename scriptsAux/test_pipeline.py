"""Smoke test del pipeline IA: imagen → detecciones → breakdown → certificado.

Funciona en modo automático: usa SAHI+Gemini si están disponibles, si no
cae al stub determinista — útil para verificar el cableado sin todas las
dependencias instaladas.

Uso:
    python scriptsAux/test_pipeline.py
    python scriptsAux/test_pipeline.py --image ai/dataset/smoke_test/images/X.jpg
    python scriptsAux/test_pipeline.py --skip-cert      # solo detección + summarize
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Asegura que la raíz del repo esté en el path para importar `ai.pipeline`
_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))

from ai.pipeline import detect_grains, generate_certificate, summarize  # noqa: E402

_IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Smoke test del pipeline SoyaLens.")
    p.add_argument(
        "--image", type=str, default=None,
        help="Ruta a la imagen. Default: primera imagen del smoke_test/."
    )
    p.add_argument("--skip-cert", action="store_true",
                   help="Omite generate_certificate() (útil sin GEMINI_API_KEY).")
    p.add_argument("--lot-id", type=str, default="L-SMOKE-001")
    p.add_argument("--supplier", type=str, default="Test Proveedor")
    return p.parse_args()


def _find_default_image() -> Path | None:
    smoke_dir = _ROOT / "ai" / "dataset" / "smoke_test" / "images"
    if not smoke_dir.is_dir():
        return None
    candidates = sorted(
        f for f in smoke_dir.iterdir()
        if f.is_file() and f.suffix.lower() in _IMAGE_EXTS
    )
    return candidates[0] if candidates else None


def main() -> int:
    args = parse_args()

    # Resolver imagen
    if args.image:
        image_path = Path(args.image).resolve()
    else:
        found = _find_default_image()
        if not found:
            print("[ERROR] No hay imágenes en ai/dataset/smoke_test/images/", file=sys.stderr)
            return 1
        image_path = found

    print(f"[INFO] Imagen: {image_path}")
    print("-" * 60)

    # 1. Detectar
    print("[PASO 1] detect_grains()")
    try:
        detections = detect_grains(str(image_path))
    except Exception as exc:
        print(f"[ERROR] detect_grains falló: {exc}", file=sys.stderr)
        return 1
    print(f"  Granos detectados: {len(detections)}")
    for d in detections[:5]:
        bbox = [round(v, 1) for v in d.bbox]
        print(f"    {d.class_name:10s}  conf={d.confidence:.2f}  bbox={bbox}")
    if len(detections) > 5:
        print(f"    ... y {len(detections) - 5} más")

    # 2. Resumir
    print("\n[PASO 2] summarize()")
    breakdown = summarize(detections)
    print(f"  Total:    {breakdown.total}")
    print(f"  Sano:     {breakdown.count_sano} ({breakdown.pct_sano}%)")
    print(f"  Partido:  {breakdown.count_partido} ({breakdown.pct_partido}%)")
    print(f"  Inmaduro: {breakdown.count_inmaduro} ({breakdown.pct_inmaduro}%)")
    print(f"  Dañado:   {breakdown.count_dañado} ({breakdown.pct_dañado}%)")
    suma = breakdown.pct_sano + breakdown.pct_partido + breakdown.pct_inmaduro + breakdown.pct_dañado
    ok = "[OK]" if abs(suma - 100.0) < 1.0 or breakdown.total == 0 else "[!]"
    print(f"  Suma pct: {suma:.2f}% {ok}")

    if args.skip_cert:
        print("\n[INFO] --skip-cert activo. Pasos 1+2 OK.")
        return 0

    # 3. Certificar
    print("\n[PASO 3] generate_certificate()")
    try:
        cert = generate_certificate(
            breakdown=breakdown,
            lot_id=args.lot_id,
            supplier=args.supplier,
            evidence_image_url="",
        )
    except Exception as exc:
        print(f"[ERROR] generate_certificate falló: {exc}", file=sys.stderr)
        return 1
    print(f"  sample_id:     {cert.sample_id}")
    print(f"  timestamp:     {cert.timestamp}")
    print(f"  verdict:       {cert.verdict}")
    print(f"  discount_pct:  {cert.discount_pct}%")
    print(f"  norm:          {cert.norm}")
    print(f"  justification: {cert.justification}")

    print("\n[OK] Pipeline ejecutado correctamente.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
