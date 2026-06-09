# 📚 Chat con tus Documentos — RAG API
### Plan de desarrollo para Claude Code
**Stack:** LlamaIndex + Groq (dev) → Claude (producción) + ChromaDB + FastAPI

---

## 🎯 Qué vamos a construir

Un sistema RAG (Retrieval-Augmented Generation) que permite:
- Subir documentos PDF o TXT
- Hacerles preguntas en lenguaje natural
- Obtener respuestas basadas **únicamente** en el contenido de esos documentos

**Caso de uso real para Forbin:** contratos, manuales técnicos, propuestas, normativas internas.

---

## 🧱 Arquitectura

```
Usuario
  │
  ▼
FastAPI (REST API)
  │
  ├── POST /upload     → Ingesta y vectoriza documentos
  ├── POST /query      → Hace preguntas al índice
  └── GET  /documents  → Lista documentos cargados
  │
  ▼
LlamaIndex
  ├── DocumentLoader   → Lee PDFs y TXTs
  ├── TextSplitter     → Divide en chunks de ~512 tokens
  ├── EmbeddingModel   → HuggingFace BAAI/bge-base-en-v1.5 (local, gratis)
  └── QueryEngine      → Orquesta retrieval + generación
  │
  ▼
ChromaDB (vector store local)
  │
  ▼
LLM
  ├── DEV:  Groq → Llama 3.3 70B (gratis)
  └── PROD: Anthropic → Claude Sonnet (API)
```

---

## 📋 Requisitos previos

### Software
- [ ] Python 3.11+
- [ ] pip o uv (gestor de paquetes)
- [ ] Git

### Cuentas y API Keys
- [ ] **Groq** (desarrollo, gratis) → https://console.groq.com
  - Crear cuenta → API Keys → Create API Key
  - Guardar como `GROQ_API_KEY`
- [ ] **Anthropic** (producción, ~$5 créditos) → https://console.anthropic.com
  - Solo necesaria al final para el deploy
  - Guardar como `ANTHROPIC_API_KEY`

---

## 📁 Estructura del proyecto

```
rag-document-chat/
├── app/
│   ├── __init__.py
│   ├── main.py           # FastAPI app y rutas
│   ├── rag_engine.py     # Lógica LlamaIndex (índice, query)
│   ├── config.py         # Variables de entorno y settings
│   └── models.py         # Schemas Pydantic
├── data/
│   └── documents/        # PDFs y TXTs subidos
├── storage/
│   └── chroma/           # Vector store persistente
├── tests/
│   └── test_api.py
├── .env                  # API keys (no subir a git)
├── .env.example          # Plantilla sin secrets
├── .gitignore
├── requirements.txt
└── README.md
```

---

## 📦 Dependencias — `requirements.txt`

```txt
# Framework RAG
llama-index==0.12.0
llama-index-llms-groq==0.3.0
llama-index-llms-anthropic==0.6.0
llama-index-embeddings-huggingface==0.4.0
llama-index-vector-stores-chroma==0.4.0

# Vector store
chromadb==0.6.0

# API
fastapi==0.115.0
uvicorn[standard]==0.32.0
python-multipart==0.0.12
pydantic==2.10.0

# Utilidades
python-dotenv==1.0.1
pypdf==5.1.0
```

---

## ⚙️ Variables de entorno — `.env`

```env
# LLM Provider: "groq" (dev) o "anthropic" (prod)
LLM_PROVIDER=groq

# API Keys
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxx
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxx   # Opcional en dev

# Modelos
GROQ_MODEL=llama-3.3-70b-versatile
ANTHROPIC_MODEL=claude-sonnet-4-5

# Embedding (siempre local, sin costo)
EMBEDDING_MODEL=BAAI/bge-base-en-v1.5

# Configuración RAG
CHUNK_SIZE=512
CHUNK_OVERLAP=50
TOP_K_RESULTS=3

# Paths
DOCUMENTS_DIR=./data/documents
CHROMA_PATH=./storage/chroma
```

---

## 🗺️ Plan de desarrollo — Fases

### Fase 1 — Setup del proyecto (30 min)
- [ ] Crear estructura de carpetas
- [ ] Inicializar git y `.gitignore`
- [ ] Crear entorno virtual e instalar dependencias
- [ ] Configurar `.env` con Groq API key

### Fase 2 — Motor RAG (2–3 horas)
- [ ] `config.py` — cargar variables de entorno
- [ ] `rag_engine.py` — clase `RAGEngine` con:
  - `load_documents(path)` — ingesta PDFs/TXTs
  - `build_index(documents)` — vectoriza y guarda en ChromaDB
  - `query(question)` — retrieval + respuesta LLM
  - `list_documents()` — documentos indexados
- [ ] Switch LLM dinámico según `LLM_PROVIDER` en `.env`

### Fase 3 — API REST con FastAPI (1–2 horas)
- [ ] `models.py` — schemas de request/response
- [ ] `main.py` — endpoints:
  - `POST /upload` — sube y procesa documento
  - `POST /query` — pregunta al sistema
  - `GET /documents` — lista documentos
  - `DELETE /documents/{id}` — elimina documento
- [ ] Manejo de errores y validaciones
- [ ] Documentación automática (Swagger en `/docs`)

### Fase 4 — Testing (1 hora)
- [ ] Test de ingesta con PDF de ejemplo
- [ ] Test de queries con preguntas conocidas
- [ ] Test de casos borde (archivo vacío, pregunta fuera de contexto)

### Fase 5 — Migración a Claude (30 min)
- [ ] Cambiar `LLM_PROVIDER=anthropic` en `.env`
- [ ] Agregar `ANTHROPIC_API_KEY`
- [ ] Verificar que todo funciona igual
- [ ] Comparar calidad de respuestas Groq vs Claude

### Fase 6 — Portfolio (1 hora)
- [ ] `README.md` completo con instrucciones, arquitectura y demo
- [ ] Capturas de pantalla de Swagger docs
- [ ] Subir a GitHub en `data-science-portfolio` o `ai-business-tools`
- [ ] Agregar a Forbin portfolio

---

## 🔄 Cómo migrar de Groq a Claude (2 líneas)

El switch está en `config.py`. Solo cambias la variable de entorno:

```bash
# Desarrollo (gratis)
LLM_PROVIDER=groq

# Producción (Claude)
LLM_PROVIDER=anthropic
```

El `rag_engine.py` detecta el provider y carga el LLM correspondiente automáticamente. No hay que tocar nada más.

---

## 💰 Estimación de costos

| Fase | Costo |
|---|---|
| Desarrollo completo con Groq | $0 |
| Testing final con Claude API | ~$1–2 USD |
| Demo a clientes con Claude | ~$0.10 por sesión |
| **Total para construir el portfolio** | **< $5 USD** |

---

## 🚀 Valor para Forbin

Este proyecto demuestra:
- **RAG pipeline** completo de producción
- **FastAPI** — base para cualquier microservicio
- **LlamaIndex** — framework líder en IA empresarial
- **ChromaDB** — manejo de vector stores
- **Claude/Groq** — integración de LLMs reales

Servicios que puedes ofrecer a PYMEs colombianas basado en esto:
- Chatbot sobre manuales de producto
- Asistente para revisión de contratos
- Sistema de consulta de normativas internas
- Base de conocimiento empresarial con IA

---

## 📝 Prompt sugerido para arrancar en Claude Code

```
Crea un proyecto Python llamado "rag-document-chat" siguiendo esta estructura 
y plan de desarrollo. Usa el archivo RAG_LLAMAINDEX_PLAN.md como referencia.

Empieza por:
1. Crear la estructura de carpetas completa
2. El archivo requirements.txt con las dependencias exactas
3. config.py con carga de variables de entorno
4. rag_engine.py con la clase RAGEngine completa
5. main.py con los 4 endpoints FastAPI

LLM provider inicial: Groq (gratis)
Embedding: HuggingFace local (sin costo)
Vector store: ChromaDB persistente en ./storage/chroma
```

---

*Generado para Forbin — Alexander Osorno*
