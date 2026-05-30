# Documentación de Inteligencia Artificial (SoyaLens)

Este archivo mantiene un registro vivo del pipeline de IA, modelos, evaluación y arquitecturas (YOLO26 + Gemini).
**Los agentes deben actualizar este documento automáticamente al realizar cambios.**

## Arquitectura Base
- **Visión:** YOLO26 (`yolo26s`) con SAHI para inferencia sobre granos densos.
- **Agente Certificador:** Gemini 3 Flash mediante SDK `google-genai`. Generación de datos estructurados Pydantic (`Certificate`).
- **Trazabilidad:** Langfuse (LLM) y Weights & Biases (Visión).
- **Firmas:** `detect_grains()`, `summarize()`, `generate_certificate()` en `ai/pipeline.py`.

## Script de Entrenamiento (`ai/train/train.py`)

- **Modelo base:** `yolo26s.pt` (transfer learning desde COCO).
- **Resolución:** 640px (mandato PROJECT.md §4). SAHI se aplica solo en inferencia.
- **Dataset:** `ai/dataset/data.yaml` — 230 train / 49 val / 50 test / 15 smoke.
- **Augmentación fuerte** (anti-overfitting, 230 imgs): HSV, rotación 360°, flip, mosaic, mixup, copy_paste.
- **Hiperparámetros base:** `epochs=150`, `patience=30`, `batch=-1` (autobatch), `seed=42`, `cos_lr=True`, `close_mosaic=10`.
- **W&B:** logging automático si `WANDB_API_KEY` está definida; degrada con gracia si falta.
- **Entregable:** `ai/weights/best.pt` (copiado automáticamente al terminar).

### Mapeo de clases (canónico — NO cambiar sin acuerdo de equipo)

| idx | `data.yaml` (dataset inglés) | `GrainClass` (español, contrato) |
|-----|------------------------------|----------------------------------|
| 0   | `broken`                     | `partido`                        |
| 1   | `immature`                   | `inmaduro`                       |
| 2   | `intact`                     | `sano`                           |
| 3   | `damaged`                    | `dañado`                         |

El mapeo se aplica **una sola vez**, en `detect_grains()` (pendiente), no en el entrenamiento.

### Comandos

```bash
# Instalar dependencias de entrenamiento:
pip install ultralytics wandb

# Entrenamiento con defaults del plan (GPU):
python ai/train/train.py

# Override para CPU / GPU limitada:
python ai/train/train.py --epochs 80 --batch 8 --device cpu

# Sin W&B (no requiere API key):
python ai/train/train.py --no-wandb
```

### Métricas del modelo (pendiente — completar tras entrenamiento)

| Métrica    | Valor |
|------------|-------|
| mAP50-95   | —     |
| mAP50      | —     |
| Fecha      | —     |
| Run W&B    | —     |

## Changelog
- *(2026-05-30) - Inicialización del documento.*
- *(2026-05-30) - Implementado `ai/train/train.py` (YOLO26s, augmentación fuerte, W&B, autobatch). Mapeo canónico de clases documentado. Creados `pyproject.toml` y `.env.example`.*
