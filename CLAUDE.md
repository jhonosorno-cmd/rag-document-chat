# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A RAG (Retrieval-Augmented Generation) API called **rag-document-chat** that lets users upload PDF/TXT documents and query them in natural language. Built for Forbin (Alexander Osorno) as a portfolio project targeting Colombian SMBs.

## Stack

- **FastAPI** — REST API layer
- **LlamaIndex** — RAG pipeline (ingestion, chunking, retrieval, generation)
- **ChromaDB** — persistent local vector store (`./storage/chroma`)
- **HuggingFace `BAAI/bge-base-en-v1.5`** — local embedding model (free, no API)
- **LLM**: Groq `llama-3.3-70b-versatile` (dev, free) / Anthropic Claude (prod)

## Commands

```bash
# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate          # Windows
source venv/bin/activate       # Unix

# Install dependencies
pip install -r requirements.txt

# Run the API server
uvicorn app.main:app --reload

# Run tests
pytest tests/
pytest tests/test_api.py::test_upload  # single test
```

API docs available at `http://localhost:8000/docs` (Swagger UI).

## Architecture

```
app/
├── main.py         # FastAPI app — POST /upload, POST /query, GET /documents, DELETE /documents/{id}
├── rag_engine.py   # RAGEngine class — core LlamaIndex logic
├── config.py       # Settings loaded from .env via pydantic-settings or python-dotenv
└── models.py       # Pydantic request/response schemas
data/documents/     # Uploaded PDFs and TXTs
storage/chroma/     # ChromaDB persistent vector store
tests/test_api.py
```

## Key Design Decisions

**LLM provider switch** — controlled entirely by `LLM_PROVIDER` in `.env`. `rag_engine.py` reads this at startup and instantiates either `LlamaIndex Groq` or `LlamaIndex Anthropic` client. No code changes needed to switch providers.

**Chunking** — 512-token chunks with 50-token overlap. `TOP_K_RESULTS=3` controls how many chunks are retrieved per query.

**Embeddings** — always local (`BAAI/bge-base-en-v1.5`), regardless of LLM provider. This keeps dev cost at $0.

## Environment Variables (`.env`)

```env
LLM_PROVIDER=groq               # "groq" or "anthropic"
GROQ_API_KEY=gsk_...
ANTHROPIC_API_KEY=sk-ant-...    # only needed when LLM_PROVIDER=anthropic
GROQ_MODEL=llama-3.3-70b-versatile
ANTHROPIC_MODEL=claude-sonnet-4-5
EMBEDDING_MODEL=BAAI/bge-base-en-v1.5
CHUNK_SIZE=512
CHUNK_OVERLAP=50
TOP_K_RESULTS=3
DOCUMENTS_DIR=./data/documents
CHROMA_PATH=./storage/chroma
```

Copy `.env.example` to `.env` and fill in at minimum `GROQ_API_KEY` for local development.
