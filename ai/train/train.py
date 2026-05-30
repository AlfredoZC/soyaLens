"""Entrenamiento del detector de granos de soya — YOLO26 (yolo26s @ 640px).

Sigue el plan en `implementation_plan.md` y el checklist del Rol IA (PROJECT.md §6.1):
  - Entrena `yolo26s` a 640px con augmentación fuerte (dataset pequeño: 230 imgs).
  - Registra el run en Weights & Biases (degrada con gracia si falta WANDB_API_KEY).
  - Copia el mejor checkpoint a `ai/weights/best.pt` (ruta que consume el Backend).

IMPORTANTE — mapeo de clases (traducción inglés → español):
  El modelo se entrena con los índices del dataset tal cual:
      0=broken, 1=immature, 2=intact, 3=damaged   (ver ai/dataset/data.yaml)
  El mapeo (traducción directa al español) se hace DESPUES, en detect_grains():
      {0: "partido", 1: "inmaduro", 2: "sano", 3: "dañado"}
  shared/schemas.py ya fue actualizado: GrainClass usa "dañado" en lugar de "hongo"
  (el dataset no tiene esa clase). Ver §1 de implementation_plan.md.

Uso:
    python ai/train/train.py                      # defaults del plan (GPU)
    python ai/train/train.py --epochs 80 --batch 8 --device cpu
    python ai/train/train.py --no-wandb           # entrena sin loguear en W&B
"""

from __future__ import annotations

import argparse
import os
import shutil
import sys
from pathlib import Path

# Cargar variables del .env automáticamente (si existe)
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parents[2] / ".env")
except ImportError:
    pass  # Si no está instalado, se usarán las vars de entorno del sistema

# --- Rutas base del repo (este archivo vive en <repo>/ai/train/train.py) ---
REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATA_YAML = REPO_ROOT / "ai" / "dataset" / "data.yaml"
DEFAULT_WEIGHTS_OUT = REPO_ROOT / "ai" / "weights" / "best.pt"

# Nombre fijo del proyecto en W&B para agrupar los runs del equipo.
WANDB_PROJECT = "soyalens-yolo26"


def parse_args() -> argparse.Namespace:
    """Define la CLI; los defaults reflejan la estrategia del implementation_plan.md."""
    p = argparse.ArgumentParser(description="Entrena yolo26s para detección de granos de soya.")
    # --- Datos y modelo ---
    p.add_argument("--data", type=Path, default=DEFAULT_DATA_YAML,
                   help="Ruta al data.yaml del dataset (default: ai/dataset/data.yaml).")
    p.add_argument("--model", type=str, default="yolo26s.pt",
                   help="Pesos base pre-entrenados (transfer learning desde COCO).")
    # --- Hiperparámetros núcleo ---
    p.add_argument("--epochs", type=int, default=150)
    p.add_argument("--imgsz", type=int, default=640, help="Mandato PROJECT.md §4. SAHI va en inferencia.")
    p.add_argument("--batch", type=int, default=-1, help="-1 = autobatch según VRAM disponible.")
    p.add_argument("--patience", type=int, default=30, help="Early stopping (anti-overfitting).")
    p.add_argument("--seed", type=int, default=42, help="Reproducibilidad.")
    p.add_argument("--device", type=str, default=None,
                   help="cuda / mps / cpu / '0'. Default: autodetección.")
    p.add_argument("--workers", type=int, default=8)
    p.add_argument("--name", type=str, default="yolo26s_soya", help="Nombre del run/carpeta de salida.")
    # --- W&B ---
    p.add_argument("--no-wandb", action="store_true", help="Desactiva el logging en Weights & Biases.")
    # --- Salida ---
    p.add_argument("--weights-out", type=Path, default=DEFAULT_WEIGHTS_OUT,
                   help="Destino del mejor checkpoint (lo consume el Backend vía MODEL_PATH).")
    p.add_argument("--no-test-eval", action="store_true",
                   help="No evaluar contra el split de test al terminar.")
    return p.parse_args()


def detect_device(requested: str | None) -> str:
    """Devuelve el mejor device disponible si no se forzó uno por CLI."""
    if requested:
        return requested
    try:
        import torch
        if torch.cuda.is_available():
            return "0"  # primera GPU CUDA
        if getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
            return "mps"
    except Exception:
        pass
    print("[AVISO] No se detectó GPU; se entrenará en CPU (lento). "
          "Considera bajar --epochs y fijar --batch.")
    return "cpu"


def maybe_init_wandb(run_name: str, disabled: bool) -> bool:
    """Autentica W&B y configura las variables de entorno para que
    Ultralytics active su integración nativa (sin add_wandb_callback,
    que rompe en ultralytics >= 8.3 por ClassificationTrainer).

    Retorna True si W&B quedó activo, False si se omitió.
    """
    if disabled:
        print("[W&B] Desactivado por --no-wandb.")
        return False
    api_key = os.environ.get("WANDB_API_KEY")
    if not api_key:
        print("[W&B] WANDB_API_KEY no encontrada; se entrena SIN logging.")
        return False
    try:
        import wandb
        wandb.login(key=api_key, relogin=True)
        # Crear el run explícitamente — Ultralytics lo detecta y envía métricas ahí
        wandb.init(
            project=WANDB_PROJECT,
            name=run_name,
            job_type="training",
            config={
                "model": "yolo26s",
                "dataset": "soyalens-granos",
                "nc": 4,
                "classes": ["broken", "immature", "intact", "damaged"],
            },
        )
        print(f"[W&B] Run creado → {wandb.run.url}")
        return True
    except Exception as exc:
        print(f"[W&B] No se pudo inicializar ({exc}). Se continúa sin logging.")
        return False


def build_train_config(args: argparse.Namespace, device: str) -> dict:
    """Construye la config de model.train con augmentación fuerte (dataset pequeño).

    Justificación de cada parámetro en implementation_plan.md §2.
    """
    return dict(
        data=str(args.data),
        project=str(REPO_ROOT / "ai" / "runs" / "detect"),  # outputs dentro de ai/
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        patience=args.patience,
        seed=args.seed,
        device=device,
        workers=args.workers,
        name=args.name,
        optimizer="auto",
        cos_lr=True,
        close_mosaic=10,     # apaga mosaic en las últimas 10 épocas (mejor regresión de cajas)
        # --- Augmentación fuerte: luz de silo variable + cámara barata + grano sin orientación ---
        hsv_h=0.015,
        hsv_s=0.7,
        hsv_v=0.4,           # clave: fluorescente vs. ambiente
        degrees=180.0,       # grano sin orientación canónica
        translate=0.1,
        scale=0.5,
        fliplr=0.5,
        flipud=0.5,
        mosaic=1.0,
        mixup=0.1,
        copy_paste=0.1,
        plots=True,
    )


def main() -> int:
    args = parse_args()

    # --- Validación de entradas ---
    if not args.data.exists():
        print(f"[ERROR] No existe el data.yaml: {args.data}", file=sys.stderr)
        return 1

    try:
        from ultralytics import YOLO
    except ImportError:
        print("[ERROR] Falta 'ultralytics'. Instala con: pip install ultralytics wandb",
              file=sys.stderr)
        return 1

    device = detect_device(args.device)
    print(f"[INFO] Device: {device} | Modelo base: {args.model} | imgsz: {args.imgsz} "
          f"| epochs: {args.epochs} | batch: {args.batch}")
    print(f"[INFO] Dataset: {args.data}")

    # --- Cargar pesos pre-entrenados (transfer learning) ---
    model = YOLO(args.model)

    # --- Tracking opcional ---
    wandb_active = maybe_init_wandb(args.name, args.no_wandb)

    # --- Entrenamiento ---
    cfg = build_train_config(args, device)
    results = model.train(**cfg)

    # `save_dir` es donde Ultralytics guardó este run (ai/runs/detect/<name>/).
    save_dir = Path(getattr(results, "save_dir", REPO_ROOT / "ai" / "runs" / "detect" / args.name))
    best_ckpt = save_dir / "weights" / "best.pt"

    # --- Evaluación opcional contra el split de test ---
    if not args.no_test_eval:
        try:
            print("[INFO] Evaluando el mejor modelo contra el split de test...")
            test_model = YOLO(str(best_ckpt)) if best_ckpt.exists() else model
            metrics = test_model.val(data=str(args.data), split="test", imgsz=args.imgsz, device=device)
            print(f"[METRICAS][test] mAP50-95={metrics.box.map:.4f} | mAP50={metrics.box.map50:.4f}")
        except Exception as exc:
            print(f"[AVISO] No se pudo evaluar en test ({exc}). Continúo igual.")

    # --- Entregable: copiar best.pt a ai/weights/best.pt ---
    if best_ckpt.exists():
        args.weights_out.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(best_ckpt, args.weights_out)
        print(f"[OK] Mejor modelo copiado a: {args.weights_out}")
    else:
        print(f"[AVISO] No se encontró best.pt en {best_ckpt}. Revisa la carpeta del run: {save_dir}",
              file=sys.stderr)

    if wandb_active:
        try:
            import wandb
            wandb.finish()
        except Exception:
            pass

    # --- Recordatorio del checklist 6.1 ---
    print("\n" + "=" * 70)
    print("  ENTRENAMIENTO TERMINADO.")
    print("  >> En cuanto el modelo sea USABLE, CONGÉLALO (PROJECT.md §6.1).")
    print("     El pipeline vivo vale más que +2% de mAP.")
    print("  >> Verifica el MAPEO DE CLASES (implementation_plan.md §1) antes")
    print("     de cablear detect_grains():  0=partido 1=inmaduro 2=sano 3=dañado")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
