# Changelog y Arquitectura — Módulo IA (SoyaLens)

## Arquitectura Base
- **Motor de Visión:** YOLO26 (pesos en `ai/weights/best.pt`).
- **Tiling (Densidad):** SAHI (Slicing Aided Hyper Inference) implementado en `detect_grains()` con tiles de 640x640 y 20% de overlap.
- **Agent LLM:** Gemini Flash (usando SDK `google-genai`) como proveedor primario en `generate_certificate()`. Si Gemini no está disponible o falla, el pipeline intenta Ollama local y finalmente cae a un certificado determinista sin LLM.
- **Descuento Determinista:** Herramienta Python `calcular_descuento()` en `ai/discount.py` para aplicar matemática exacta (norma IBNORCA NB 339) sin alucinaciones del LLM.
- **Observabilidad:** Langfuse configurado para trazar costos y prompts del LLM.

## Registro de Cambios (Changelog)

### [2026-05-30] Sprint 1 — Pipeline Base Completado
- Se implementó la lógica de umbrales en `ai/discount.py`.
- Se codificó `ai/pipeline.py` implementando las 3 funciones exigidas por el Backend (`detect_grains`, `summarize`, `generate_certificate`).
- Se corrigió el mapeo de clases para traducir del dataset en inglés al esquema en español (`GrainClass`).
- Se añadió un script de prueba E2E (`scriptsAux/test_pipeline.py`).
- **Estado actual:** El pipeline es capaz de procesar una imagen real y emitir un certificado completo en formato JSON validado por Pydantic.

### [2026-05-31] Sprint 2 — Corrección de Domain Shift y Mapeo Adaptativo
- Se detectó un problema de domain shift al inferir sobre imágenes tomadas con fondo claro/madera (pruebas locales del usuario).
- Se implementó la detección automática de fondo tipo madera en `ai/pipeline.py` (usando el promedio del canal HSV).
- Se aplicó un mapeo de clases adaptativo para corregir la clasificación errónea producida por el cambio de contraste del fondo, asegurando resultados precisos en la demo con fondo oscuro y en pruebas con fondo claro.

### [2026-05-31] Sprint 2 — Prioridad de LLM para Certificados
- Se corrigió la prioridad de `generate_certificate()` para usar Gemini Flash como proveedor principal.
- Si Gemini no está configurado o falla durante la generación, el pipeline intenta Ollama local.
- Si no hay LLM disponible o Ollama falla, se emite un certificado determinista usando `calcular_descuento()` y una justificación técnica fija.
