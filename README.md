# rag-document-chat

![CI](https://github.com/jhonosorno-cmd/rag-document-chat/actions/workflows/ci.yml/badge.svg)

A production-ready RAG (Retrieval-Augmented Generation) system that lets you upload PDF and TXT documents and query them in natural language. Includes a REST API, a terminal CLI with FORBIN branding, and a Gradio web UI with demo modes for consulting pitches.

Built as a portfolio project demonstrating a full AI pipeline with FastAPI, LlamaIndex, and ChromaDB.

## Interfaces

| Interface | Command | Best for |
|---|---|---|
| REST API | `uvicorn app.main:app --reload` | Developers, integrations |
| Terminal CLI | `python chat.py` | Local use, consulting demos |
| Web UI | `python web.py` | Non-technical users, client meetings |

## Quick start

```bash
# 1. Clone and create virtual environment
git clone https://github.com/jhonosorno-cmd/rag-document-chat
cd rag-document-chat
python -m venv venv
venv\Scripts\activate       # Windows
source venv/bin/activate    # Unix

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env and add your GROQ_API_KEY (free at console.groq.com)

# 4. Pick your interface
uvicorn app.main:app --reload   # REST API → http://localhost:8000/docs
python chat.py                  # Terminal CLI
python web.py                   # Web UI → http://localhost:7860
```

## Terminal CLI

```bash
python chat.py                   # Normal mode
python chat.py --demo legal      # Demo mode — legal vertical
python chat.py --demo industrial # Demo mode — industrial vertical
```

Commands inside the CLI:

| Command | Action |
|---|---|
| `/upload <path>` | Add a PDF or TXT to the index |
| `/list` | Show indexed documents |
| `/delete <name>` | Remove a document |
| `/demo legal\|industrial` | Load demo docs + suggested questions |
| `1`–`9` | Send the Nth suggested demo question |
| `/clear` | Clear screen |
| `/help` | Show command list |
| `/quit` | Exit |

## Web UI

```bash
python web.py                    # Local → http://localhost:7860
python web.py --demo legal       # With demo panel and suggested questions
python web.py --share            # Public Gradio URL (for remote demos)
python web.py --port 8080        # Custom port (also reads PORT env var)
```

Two-column layout: document upload + index on the left, chat on the right.

## REST API

**Upload a document**
```bash
curl -X POST http://localhost:8000/upload \
  -F "file=@contract.pdf"
# {"message":"Ingested successfully","filename":"contract.pdf","chunks_created":47}
```

**Query the document**
```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "What are the payment terms?"}'
# {"answer":"Payment is due within 30 days of invoice...","sources":["contract.pdf"]}
```

**List indexed documents**
```bash
curl http://localhost:8000/documents
# [{"filename":"contract.pdf","id":"contract.pdf"}]
```

Swagger UI available at `http://localhost:8000/docs`.

## Architecture

```
User
 │
 ├── chat.py (CLI)  ──┐
 ├── web.py (Gradio) ─┤
 └── FastAPI (REST) ──┤
                      ▼
                 RAGEngine (LlamaIndex)
                  ├── SimpleDirectoryReader  → loads PDFs and TXTs
                  ├── SentenceSplitter       → 512-token chunks, 50-token overlap
                  ├── HuggingFace Embeddings → BAAI/bge-base-en-v1.5 (local, free)
                  └── VectorStoreIndex       → retrieval + LLM generation
                      │
                      ▼
                 ChromaDB (persistent local vector store)
                      │
                      ▼
                 LLM
                  ├── DEV:  Groq  → Llama 3.3 70B (free)
                  └── PROD: Anthropic → Claude Sonnet
```

## Stack

| Component | Technology |
|---|---|
| API | FastAPI 0.115 |
| RAG pipeline | LlamaIndex 0.14 |
| Vector store | ChromaDB 1.x |
| Embeddings | `BAAI/bge-base-en-v1.5` (local) |
| LLM (dev) | Groq `llama-3.3-70b-versatile` |
| LLM (prod) | Anthropic Claude Sonnet |
| CLI | rich |
| Web UI | Gradio 6.x |
| Validation | Pydantic v2 |
| Testing | pytest + pytest-asyncio |

## Switching LLM provider

The switch is a single env var — no code changes needed:

```env
# Development (free)
LLM_PROVIDER=groq
GROQ_API_KEY=gsk_...

# Production (Claude)
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-...
```

## Running tests

```bash
pytest tests/
# 18 passed
```

## Design decisions

**Local embeddings** — `BAAI/bge-base-en-v1.5` runs on CPU via HuggingFace. Zero embedding cost in dev and prod.

**ChromaDB persistence** — vectors are stored in `./storage/chroma` and survive server restarts. Re-uploading the same file is a no-op (re-ingest guard by filename).

**Provider abstraction** — `LLM_PROVIDER` in `.env` is the only switch. `rag_engine.py` instantiates the right LlamaIndex client at startup.

**Security** — uploaded filenames are sanitized to prevent path traversal. Extension validated server-side in both the REST API and the web UI.

**Demo mode** — `demo/legal/` and `demo/industrial/` hold pre-loaded documents and suggested questions per vertical. Designed for consulting pitches where both a non-technical gerente and a CTO are in the room.

## Use cases for SMBs

- Chat with contracts and legal documents
- Query technical manuals and product specs
- Search internal compliance or policy documents
- Build a knowledge base from company documentation

---

*Built with [LlamaIndex](https://www.llamaindex.ai/) · [FastAPI](https://fastapi.tiangolo.com/) · [ChromaDB](https://www.trychroma.com/) · [Gradio](https://www.gradio.app/)*
