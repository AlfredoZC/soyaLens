# SoyaLens — Documento Maestro del Proyecto
### Single Source of Truth (Fuente Única de Verdad)

> **Hackathon Build With AI 2026 · Mención: INDUSTRIA (Control de Calidad)**
> Este documento es la verdad oficial del proyecto. Si algo no está aquí, no existe.
> Todos construyen **contra los contratos definidos en la Sección 5**. Nadie cambia un contrato sin avisar a todo el equipo.

---

## 0. CÓMO USAR ESTE DOCUMENTO (léelo primero)

Este proyecto se construye en 3 partes en paralelo (IA, Backend, Frontend). El mayor riesgo no es la tecnología: es que las 3 partes **no encajen** al unirlas. Para evitarlo:

1. **Los CONTRATOS (Sección 5) son sagrados.** Son los "enchufes" que conectan las partes: los modelos de datos, la API y la base de datos. Mientras todos respeten el mismo enchufe, las piezas encajan aunque se construyan por separado.
2. **Cada quien lee TODO este documento una vez, y luego trabaja sobre la sección de su rol (Sección 6).**
3. **Regla de oro al usar agentes de IA en terminal (Cursor, Claude Code, etc.):**
   - ❌ NUNCA digas: *"hazme el backend de esta idea"*. El agente inventará su propio diseño y no encajará con lo demás.
   - ✅ SIEMPRE haz: pega **este documento** (o tu sección + la Sección 5 de contratos) en el contexto del agente, y di: *"Implementa EXACTAMENTE el endpoint `POST /api/v1/analyze` según este contrato, usando estos schemas, sin inventar campos nuevos."*
   - El archivo `shared/schemas.py` (Sección 5.1) es la fuente de verdad del código. Apunta tu agente a ese archivo.

---

## 1. CONTEXTO DEL PROYECTO (el porqué)

**El problema.** Santa Cruz produce más del 99% de los ~3 millones de toneladas de soya de Bolivia. En zafra, un silo recibe hasta 300 camiones al día. El precio de cada camión (miles de dólares) se decide con un descuento por "grano dañado", y ese análisis es **100% manual**: un técnico separa 100 g de soya con una espátula bajo un tubo fluorescente. Toma ~15 minutos por camión, fatiga la vista, genera filas de kilómetros, y abre la puerta a la subjetividad y la corrupción (sobornos para aprobar grano podrido).

**La brecha.** En el primer mundo esto se resuelve con clasificadoras ópticas (Bühler, Tomra) de ~medio millón de dólares. Los acopiadores y cooperativas locales no pueden pagarlas, así que siguen con la espátula.

**Nuestra solución (SoyaLens).** Un auditor visual por IA: el técnico vuelca la muestra bajo una cámara barata, el sistema la escanea, identifica cada anomalía (hongo, partido, inmaduro) y emite un **certificado de calidad objetivo, auditable y con evidencia** en ~2 segundos. La misma auditoría óptica industrial, por una fracción del costo.

**Triple impacto.** *Profit:* elimina mermas, paga el precio justo por la calidad real, libera horas-hombre. *Planet:* aísla a tiempo el grano con hongo que podría pudrir tanques enteros, reduce CO₂ de camiones en fila. *People:* transparenta el mercado para el pequeño productor y libera al técnico de una tarea que destruye su agudeza visual.

---

## 2. QUÉ VAMOS A CONSTRUIR (alcance del MVP)

**Modelo:** SaaS **cloud-first**. El modelo de IA vive en NUESTRO servidor. El cliente solo sube una foto vía web y recibe el certificado. (El "modo edge offline" es roadmap futuro, NO se construye en el hackathon.)

**Flujo completo del MVP (esto es lo que debe funcionar el día de la demo):**

```
1. El usuario sube/captura una foto de la bandeja de soya  (FRONTEND)
2. La foto llega al servidor                                (BACKEND)
3. El servidor guarda la foto como evidencia               (BACKEND → Supabase Storage)
4. El modelo detecta y clasifica cada grano                (IA: YOLO26 + SAHI)
5. Se resume en porcentajes por clase                      (IA)
6. El agente LLM genera el certificado normado + descuento (IA: Gemini)
7. Se guarda el resultado en la base de datos              (BACKEND → Supabase)
8. El frontend muestra el certificado bonito               (FRONTEND)
9. El dashboard muestra el historial y las métricas del día(FRONTEND)
```

**Definition of Done del MVP:** subir una foto real desde el frontend → recibir un certificado correcto → verlo aparecer en el dashboard. Si eso funciona de punta a punta, el MVP está listo.

**Fuera de alcance (NO construir):** modo offline/edge, app móvil nativa, multi-idioma, pagos reales, autenticación compleja (un login simple basta o ninguno para la demo).

---

## 3. ARQUITECTURA (cómo se conecta todo)

```
   ┌─────────────────────┐
   │      FRONTEND        │   captura/upload, certificado, dashboard
   │ (Streamlit o web)    │
   └──────────┬──────────┘
              │  HTTP (JSON) — contrato Sección 5.3
              ▼
   ┌─────────────────────┐
   │   BACKEND (FastAPI)  │   orquesta todo
   │  POST /analyze, etc. │
   └───┬───────────┬─────┘
       │           │  llama funciones Python — firmas Sección 6.1
       │           ▼
       │   ┌─────────────────────┐
       │   │   MÓDULO IA          │
       │   │  vision.py (YOLO26   │
       │   │   + SAHI)            │
       │   │  agent.py (Gemini)   │
       │   └─────────────────────┘
       ▼
   ┌─────────────────────┐
   │   SUPABASE (nube)    │   Postgres (resultados) + Storage (fotos)
   │                      │   + Realtime (dashboard en vivo)
   └─────────────────────┘
```

**Punto clave:** el Frontend NO conoce a la IA. Solo habla con el Backend vía la API. El Backend NO conoce los detalles de la IA, solo llama 3 funciones. Esto permite que los 3 trabajen en paralelo sin pisarse.

---

## 4. STACK TECNOLÓGICO

| Capa | Herramienta | Responsable |
|---|---|---|
| Lenguaje/entorno | Python 3.12 + uv + Ruff | Todos |
| Visión | Ultralytics **YOLO26** (`yolo26s`) | IA |
| Tiling | **SAHI** | IA |
| Soporte visión | OpenCV, PyTorch | IA |
| Dataset | **Roboflow** | IA |
| Tracking ML | **Weights & Biases** | IA |
| Agente/Certificado | **Gemini 3 flash** (`google-genai`) + Pydantic | IA |
| Observabilidad LLM | **Langfuse** | IA |
| Backend/API | **FastAPI** + Uvicorn | Backend |
| Base de datos | **Supabase** (Postgres + Storage + Realtime) | Backend |
| Frontend | **Streamlit** (rápido) o web custom — ABIERTO | Frontend |
| Empaquetado | **Docker + docker-compose** | Backend |
| CI/Calidad | GitHub Actions + pytest | Backend + IA |

---

## 5. CONTRATOS (la cola que une todo) ⚠️ NO MODIFICAR SIN AVISAR

### 5.1 Modelos de datos compartidos → `shared/schemas.py`

Este archivo lo crea UNA persona al inicio y **todos lo importan**. Backend e IA usan estas MISMAS clases. El Frontend las usa como referencia del JSON que recibe.

```python
# shared/schemas.py
from pydantic import BaseModel
from typing import Literal, Optional
from datetime import datetime

# Las 4 clases de grano (NO agregar más sin acuerdo de equipo)
GrainClass = Literal["sano", "partido", "hongo", "inmaduro"]

class Detection(BaseModel):
    class_name: GrainClass
    confidence: float
    bbox: list[float]              # [x1, y1, x2, y2]

class ClassBreakdown(BaseModel):
    total: int
    count_sano: int
    count_partido: int
    count_hongo: int
    count_inmaduro: int
    pct_sano: float
    pct_partido: float
    pct_hongo: float
    pct_inmaduro: float

class Certificate(BaseModel):
    sample_id: str
    timestamp: datetime
    lot_id: Optional[str] = None
    supplier: Optional[str] = None
    breakdown: ClassBreakdown
    verdict: Literal["aprobado", "con_descuento", "rechazado"]
    discount_pct: float            # 0.0 a 100.0
    norm: str                      # ej. "IBNORCA NB 339"
    justification: str             # texto del agente, en español
    evidence_image_url: str
```

### 5.2 Esquema de la base de datos → Supabase

**Tabla `samples`** (la crea el Backend en el SQL Editor de Supabase):

```sql
create table samples (
  id            uuid primary key default gen_random_uuid(),
  created_at    timestamptz default now(),
  lot_id        text,
  supplier      text,
  evidence_url  text,
  total_grains  int,
  pct_sano      numeric,
  pct_partido   numeric,
  pct_hongo     numeric,
  pct_inmaduro  numeric,
  verdict       text,
  discount_pct  numeric,
  norm          text,
  justification text
);
```

**Storage bucket:** crear uno llamado `evidence` (público para la demo).

### 5.3 Contrato de la API → lo que el Frontend consume y el Backend implementa

Base URL local: `http://localhost:8000`

```
POST /api/v1/analyze
  Body: multipart/form-data
        image    (archivo, requerido)
        lot_id   (texto, opcional)
        supplier (texto, opcional)
  Respuesta 200: objeto Certificate (ver 5.1) en JSON

GET /api/v1/samples?limit=50
  Respuesta 200: { "items": [ {id, created_at, lot_id, supplier,
                   verdict, pct_hongo, discount_pct, evidence_url} ],
                   "total": int }

GET /api/v1/samples/{id}
  Respuesta 200: objeto Certificate completo

GET /api/v1/stats/today
  Respuesta 200: { "total_samples": int, "approved": int,
                   "with_discount": int, "rejected": int,
                   "avg_pct_hongo": float }

GET /health
  Respuesta 200: { "status": "ok" }

Notas: habilitar CORS para que el frontend pueda llamar.
       Errores devuelven { "error": "mensaje" } con código 4xx/5xx.
```

### 5.4 Variables de entorno → `.env` (cada quien crea su `.env` local desde `.env.example`)

```
GEMINI_API_KEY=...        # IA + Backend
SUPABASE_URL=...          # Backend
SUPABASE_KEY=...          # Backend (service role)
WANDB_API_KEY=...         # IA
LANGFUSE_PUBLIC_KEY=...   # IA
LANGFUSE_SECRET_KEY=...   # IA
MODEL_PATH=ai/weights/best.pt   # Backend (para cargar el modelo)
```

---

## 6. ROLES Y TAREAS

> Cada rol tiene: su responsabilidad, lo que debe ENTREGAR a los demás (su "enchufe"), y su checklist.

### 6.1 ROL: DESARROLLADOR DE IA (Visión + Agente)

**Responsabilidad:** que el modelo detecte granos y que el agente emita el certificado. Entregar 3 funciones que el Backend pueda llamar.

**Lo que DEBES exponer al Backend (firmas exactas — `ai/pipeline.py`):**
```python
def detect_grains(image_path: str) -> list[Detection]: ...
def summarize(detections: list[Detection]) -> ClassBreakdown: ...
def generate_certificate(breakdown: ClassBreakdown,
                         lot_id: str | None,
                         supplier: str | None) -> Certificate: ...
```
> El Backend solo conoce estas 3 funciones. Por dentro haz lo que quieras, pero la firma NO cambia.

**Checklist:**
- [ ] Conseguir dataset en Roboflow: 4 clases (`sano`, `partido`, `hongo`, `inmaduro`). Usa un dataset de Roboflow Universe + etiqueta 80–150 fotos de NUESTRA muestra real bajo NUESTRA cámara/luz. Augmentación fuerte.
- [ ] Entrenar `yolo26s` (640px). Registrar el run en Weights & Biases. Guardar el mejor modelo en `ai/weights/best.pt`.
- [ ] **En cuanto tengas un modelo usable, CONGÉLALO.** No busques perfección; el pipeline vivo vale más que +2% de mAP.
- [ ] Implementar `detect_grains()` usando YOLO26 + SAHI (tiling) para los granos densos.
- [ ] Implementar `summarize()` → cuenta por clase y calcula porcentajes.
- [ ] Implementar `generate_certificate()` con Gemini 3 (function calling + structured output con Pydantic). Define una herramienta `calcular_descuento(norm, pcts)` determinista en Python (la matemática del descuento NO la inventa el LLM; el LLM la llama). El agente devuelve veredicto + descuento + justificación en español.
- [ ] Conectar Langfuse para trazar cada certificado generado.
- [ ] 5–10 evals del agente (pytest): JSON de detección → certificado esperado.
- [ ] Anotar métricas (mAP, latencia) + benchmark YOLO26 vs RT-DETR para el documento técnico.

**Cómo entregar mientras tanto:** el primer día, sube una versión "stub" de las 3 funciones que devuelva datos falsos pero **con el schema correcto**, para que el Backend pueda integrar sin esperar a que termine el entrenamiento.

---

### 6.2 ROL: BACKEND (FastAPI + Supabase)

**Responsabilidad:** el servidor que recibe la foto, orquesta la IA, guarda en Supabase y devuelve el certificado. Implementar exactamente el contrato 5.3.

**De qué dependes:** las 3 funciones de IA (6.1). Mientras la IA no esté lista, **úsalas mockeadas** (un stub que devuelve un `Certificate` falso que cumpla el schema). Así no te bloqueas.

**Checklist:**
- [ ] Crear el proyecto FastAPI (`backend/main.py`) con uv.
- [ ] Importar los schemas de `shared/schemas.py` (no redefinas modelos).
- [ ] Crear la tabla `samples` y el bucket `evidence` en Supabase (SQL de 5.2).
- [ ] Implementar `POST /api/v1/analyze`:
      recibir imagen → subir a Supabase Storage (obtener `evidence_url`) → llamar `detect_grains()` → `summarize()` → `generate_certificate()` → insertar fila en `samples` → devolver el `Certificate`.
- [ ] Implementar `GET /api/v1/samples`, `GET /api/v1/samples/{id}`, `GET /api/v1/stats/today`, `GET /health`.
- [ ] Habilitar CORS (para el frontend).
- [ ] Manejo de errores: respuestas `{ "error": ... }` claras.
- [ ] Escribir el `Dockerfile` del backend y el servicio en `docker-compose.yml`.
- [ ] Smoke test: un `pytest` que sube una imagen de prueba a `/analyze` y verifica que la respuesta cumple el schema `Certificate`.

**Prompt sugerido para tu agente de terminal:**
> "Implementa un servidor FastAPI con el endpoint `POST /api/v1/analyze` que recibe un archivo de imagen, lo sube a Supabase Storage, llama a las funciones `detect_grains`, `summarize` y `generate_certificate` del módulo `ai.pipeline`, guarda el resultado en la tabla `samples` y devuelve un objeto `Certificate`. Usa los modelos Pydantic de `shared/schemas.py`. NO inventes campos nuevos."

---

### 6.3 ROL: FRONTEND (Streamlit o web — decisión abierta)

**Responsabilidad:** la cara del producto. 3 pantallas: captura → certificado → dashboard.

**De qué dependes:** SOLO del contrato de API (5.3). **No necesitas esperar a nadie**: empieza con un `Certificate` JSON de ejemplo (mock) y arma toda la UI; al final cambias el mock por la llamada real al backend.

**Checklist:**
- [ ] Pantalla de **captura**: subir foto o usar cámara → botón "Analizar" → `POST /api/v1/analyze`. Diseño minimalista a propósito (una acción, dos segundos): pensado para un operario apurado en un silo. Botón grande, veredicto claro (verde/rojo).
- [ ] Render del **certificado** (este es el artefacto estrella, dale el mejor diseño): veredicto, % por clase, descuento, norma, justificación del agente, foto de evidencia, lote, fecha/hora.
- [ ] **Dashboard**: lista de muestras (`GET /samples`) + métricas del día (`GET /stats/today`). Si usas Supabase Realtime, que se actualice en vivo.
- [ ] Estados de carga y de error.
- [ ] (Si hay tiempo) tematizar para que no se vea "por defecto".

**Mock para empezar sin bloquearte** (pega esto como respuesta de ejemplo):
```json
{
  "sample_id": "demo-001", "timestamp": "2026-05-31T09:00:00",
  "lot_id": "L-204", "supplier": "Coop. San Juan",
  "breakdown": {"total": 312, "count_sano": 290, "count_partido": 10,
    "count_hongo": 8, "count_inmaduro": 4, "pct_sano": 92.9,
    "pct_partido": 3.2, "pct_hongo": 2.6, "pct_inmaduro": 1.3},
  "verdict": "con_descuento", "discount_pct": 4.5, "norm": "IBNORCA NB 339",
  "justification": "La muestra presenta 2.6% de grano con hongo, superando el umbral de 2%. Se aplica un descuento de 4.5%.",
  "evidence_image_url": "https://placehold.co/600x400"
}
```

---

### 6.4 NOTA: ENTREGABLES DE NEGOCIO/DOCUMENTOS

Pediste 3 roles técnicos, pero **OJO**: hay entregables que valen puntos y no son código (Lean Canvas, FODA, PESTEL, análisis financiero, documento técnico, slides, video). Asigna esto a quien tenga menos carga técnica, o repártelo. **No puede quedar sin dueño** — el Lean Canvas y el análisis financiero hoy están vacíos.

---

## 7. PLAN DE INTEGRACIÓN (cómo unir todo sin que explote)

**Orden obligatorio:**
1. **Hora 0 (TODOS juntos, 30 min):** leer este doc. Crear el repo, la estructura de carpetas (Sección 8) y `shared/schemas.py`. Acordar que los contratos NO se tocan. Repartir los `.env`.
2. **Trabajo en paralelo (con mocks):**
   - IA entrena y publica las 3 funciones (primero stubs, luego reales).
   - Backend implementa endpoints usando stubs de IA.
   - Frontend arma la UI usando el JSON mock.
3. **Integración 1:** Backend reemplaza los stubs por las funciones reales de IA.
4. **Integración 2:** Frontend apunta al backend real (quita el mock).
5. **Smoke test end-to-end:** subir una foto real → certificado correcto → aparece en dashboard. ✅ = MVP listo.
6. **Pulido + grabar video + ensayar pitch.**

**Regla anti-caos:** nadie pasa a "su versión bonita" hasta que el flujo end-to-end funcione una vez. **Primero que funcione, luego que impresione.**

---

## 8. ESTRUCTURA DEL REPOSITORIO (monorepo)

```
soyalens/
├── README.md              # info del proyecto (requisito del hackathon)
├── PROJECT.md             # ESTE documento
├── docker-compose.yml
├── .env.example
├── shared/
│   └── schemas.py         # ⚠️ modelos compartidos (5.1) — fuente de verdad
├── ai/                    # dueño: IA
│   ├── pipeline.py        # detect_grains, summarize, generate_certificate
│   ├── train/             # scripts de entrenamiento
│   ├── evals/             # tests del agente
│   └── weights/best.pt
├── backend/               # dueño: Backend
│   ├── main.py
│   └── db.py
├── frontend/              # dueño: Frontend
│   └── (app.py o proyecto web)
└── docs/                  # dueño: Negocio/Docs
    ├── documento_tecnico.*
    ├── lean_canvas.*
    └── slides.*
```

**Git para equipo junior:** cada rol trabaja en su rama (`ai`, `backend`, `frontend`), hace commits seguidos y mergea a `main` seguido. Hagan `git pull` antes de empezar cada sesión. Cada quien toca SOLO su carpeta; `shared/schemas.py` se cambia solo en grupo.

---

## 9. CHECKLIST DE ENTREGABLES DEL HACKATHON

> **Deadline duro: domingo 31, suben desde las 09:00, máximo 10:00. Sin prórroga. Quien no sube → fuera de fase 1.** Trata las 09:00 como tu cierre real.

- [ ] **Documento técnico**: investigación, problema, solución, arquitectura, aplicación de IA, FODA, PESTEL, Lean Canvas, análisis financiero, impacto.
- [ ] **MVP funcional** (flujo end-to-end de la Sección 2) + demo a prueba de balas (snapshot) + plan B grabado.
- [ ] **Repo GitHub público**: todos como colaboradores; README con explicación, arquitectura, tecnologías, imágenes, instrucciones de ejecución, nombre del equipo e integrantes; commits durante el evento.
- [ ] **Video pitch ≤ 2 min** (gancho de la espátula + demo del certificado).
- [ ] **Presentación** (PowerPoint/Canva/Gamma): problema → usuario → solución → demo → tecnología → impacto → próximos pasos.
- [ ] **Pitch en vivo** ensayado 3 veces, en tiempo.
- [ ] **Bonus (+10):** CI con evals + agente funcionando en vivo = demuestra que es 100% aplicable.

---

## 10. CRONOGRAMA (lo que queda)

| Bloque | Quién | Qué |
|---|---|---|
| Ahora | Todos | Leer doc, crear repo + `shared/schemas.py`, repartir `.env` |
| Sábado tarde/noche | IA | Dataset + entrenar + stubs de las 3 funciones |
| Sábado tarde/noche | Backend | Endpoints con stubs + Supabase |
| Sábado tarde/noche | Frontend | UI con mock JSON |
| Sábado noche | Negocio | Lean Canvas, FODA, PESTEL, financiero, README |
| Sábado noche / domingo madrugada | Backend + IA | Integración 1 (IA real en backend) |
| Domingo madrugada | Frontend | Integración 2 (backend real) + smoke test E2E |
| Domingo madrugada | Todos | Pulido, grabar video, ensayar pitch |
| **Domingo 09:00** | Todos | **SUBIR TODO** |

---

*Cualquier duda de "¿esto encaja con lo de los demás?" → la respuesta está en la Sección 5. Si no está ahí, se habla en grupo antes de codear.*
