# Changelog y Arquitectura — Módulo IA (SoyaLens)

## Arquitectura Base
- **Motor de Visión:** YOLO26 (pesos en `ai/weights/best.pt`).
- **Tiling (Densidad):** SAHI (Slicing Aided Hyper Inference) implementado en `detect_grains()` con tiles de 640x640 y 20% de overlap.
- **Agent LLM:** Gemini 3.5 Flash (usando SDK `google-genai`), implementado en `generate_certificate()`.
- **Descuento Determinista:** Herramienta Python `calcular_descuento()` en `ai/discount.py` para aplicar matemática exacta (norma IBNORCA NB 339) sin alucinaciones del LLM.
- **Observabilidad:** Langfuse configurado para trazar costos y prompts del LLM.

## Registro de Cambios (Changelog)

### [2026-05-30] Sprint 1 — Pipeline Base Completado
- Se implementó la lógica de umbrales en `ai/discount.py`.
- Se codificó `ai/pipeline.py` implementando las 3 funciones exigidas por el Backend (`detect_grains`, `summarize`, `generate_certificate`).
- Se corrigió el mapeo de clases para traducir del dataset en inglés al esquema en español (`GrainClass`).
- Se añadió un script de prueba E2E (`scriptsAux/test_pipeline.py`).
- **Estado actual:** El pipeline es capaz de procesar una imagen real y emitir un certificado completo en formato JSON validado por Pydantic.
