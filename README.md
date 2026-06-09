# rag-document-chat

A production-ready RAG (Retrieval-Augmented Generation) REST API that lets you upload PDF and TXT documents and query them in natural language. Built as a portfolio project demonstrating a full AI pipeline with FastAPI, LlamaIndex, and ChromaDB.

## What it does

Upload your documents, ask questions, get answers grounded in the document content — not hallucinations.

```
POST /upload   → ingest a PDF or TXT into the vector store
POST /query    → ask a question, get an answer + source references
GET  /documents → list all indexed documents
DELETE /documents/{id} → remove a document from the index
```

## Architecture

```
User
 │
 ▼
FastAPI (REST API)
 │
 ▼
LlamaIndex
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
| Validation | Pydantic v2 |
| Testing | pytest + pytest-asyncio |

## Quick start

```bash
# 1. Clone and create virtual environment
git clone https://github.com/your-username/rag-document-chat
cd rag-document-chat
python -m venv venv
venv\Scripts\activate       # Windows
source venv/bin/activate    # Unix

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env and add your GROQ_API_KEY (free at console.groq.com)

# 4. Run the server
uvicorn app.main:app --reload
```

API docs available at `http://localhost:8000/docs`

## API usage

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
# 15 passed in ~3s
```

## Design decisions

**Local embeddings** — `BAAI/bge-base-en-v1.5` runs on CPU via HuggingFace. Zero embedding cost in dev and prod.

**ChromaDB persistence** — vectors are stored in `./storage/chroma` and survive server restarts. Re-uploading the same file is a no-op (re-ingest guard by filename).

**Provider abstraction** — `LLM_PROVIDER` in `.env` is the only switch. `rag_engine.py` instantiates the right LlamaIndex client at startup.

**Security** — uploaded filenames are sanitized to prevent path traversal. Only `data/documents/` is writable by the upload endpoint.

## Use cases for SMBs

- Chat with contracts and legal documents
- Query technical manuals and product specs
- Search internal compliance or policy documents
- Build a knowledge base from company documentation

---

*Built with [LlamaIndex](https://www.llamaindex.ai/) · [FastAPI](https://fastapi.tiangolo.com/) · [ChromaDB](https://www.trychroma.com/)*
