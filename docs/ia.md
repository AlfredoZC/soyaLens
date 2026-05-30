# Documentación de Inteligencia Artificial (SoyaLens)

Este archivo mantiene un registro vivo del pipeline de IA, modelos, evaluación y arquitecturas (YOLO26 + Gemini).
**Los agentes deben actualizar este documento automáticamente al realizar cambios.**

## Arquitectura Base
- **Visión:** YOLO26 (`yolo26s`) con SAHI para inferencia sobre granos densos.
- **Agente Certificador:** Gemini 3 Flash mediante SDK `google-genai`. Generación de datos estructurados Pydantic (`Certificate`).
- **Trazabilidad:** Langfuse (LLM) y Weights & Biases (Visión).
- **Firmas:** `detect_grains()`, `summarize()`, `generate_certificate()` en `ai/pipeline.py`.

## Changelog
- *(2026-05-30) - Inicialización del documento.*
