# CLI + Web UI + Demo Mode — Design Spec

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a beautiful terminal CLI and a Gradio web UI to the existing RAG API, both with demo modes for consulting pitches targeting legal and industrial verticals.

**Architecture:** Two new entry points (`chat.py`, `web.py`) that import `RAGEngine` directly — no HTTP layer. A `demo/` directory holds pre-loaded documents and suggested questions per vertical.

**Tech Stack:** `rich` (CLI), `gradio` (web UI), existing `app/rag_engine.py`

**Business context:** Consulting model. Demo audience is both non-technical gerentes and CTOs. Local demo on laptop + deployable URL for post-meeting client evaluation.

---

## Files

| File | Action | Responsibility |
|---|---|---|
| `chat.py` | Create | CLI entry point — logo, chat loop, commands |
| `web.py` | Create | Gradio entry point — upload, chat, sources |
| `demo/legal/preguntas.txt` | Create | Suggested questions for legal vertical |
| `demo/legal/README.txt` | Create | Instructions for the consultant |
| `demo/industrial/preguntas.txt` | Create | Suggested questions for industrial vertical |
| `demo/industrial/README.txt` | Create | Instructions for the consultant |
| `requirements.txt` | Modify | Add `gradio` |
| `app/rag_engine.py` | No change | Existing RAGEngine used as-is |

---

## CLI (`chat.py`)

### Startup

Running `python chat.py` shows:

```
███████╗ ██████╗ ██████╗ ██████╗ ██╗███╗   ██╗
██╔════╝██╔═══██╗██╔══██╗██╔══██╗██║████╗  ██║
█████╗  ██║   ██║██████╔╝██████╔╝██║██╔██╗ ██║
██╔══╝  ██║   ██║██╔══██╗██╔══██╗██║██║╚██╗██║
██║     ╚██████╔╝██║  ██║██████╔╝██║██║ ╚████║
╚═╝      ╚═════╝ ╚═╝  ╚═╝╚═════╝ ╚═╝╚═╝  ╚═══╝

  Document Chat  ·  by Forbin  ·  v1.0
  ✓  2 documentos indexados
```

Running `python chat.py --demo legal` additionally shows:

```
  ◆  Modo demo — Sector Legal
  Documentos cargados: contrato_arrendamiento.pdf, ...
  Preguntas sugeridas:
    1. ¿Cuál es el plazo del contrato?
    ...
```

### Commands

| Command | Behavior |
|---|---|
| `/upload <ruta>` | Copies file to `data/documents/`, calls `engine.ingest_document()`, shows chunk count |
| `/list` | Calls `engine.list_documents()`, prints table |
| `/delete <nombre>` | Calls `engine.delete_document()`, removes file from disk |
| `/demo legal` | Ingests files from `demo/legal/`, prints suggested questions |
| `/demo industrial` | Ingests files from `demo/industrial/`, prints suggested questions |
| `/clear` | Clears screen, reprints logo |
| `/help` | Reprints command list |
| `/quit` | Exits |

### Query interaction

Any non-command input is treated as a question:
1. Live spinner: `⠸ Pensando...`
2. Answer displayed in a `rich` rounded panel with blue border
3. Sources listed below the panel as `fuentes  archivo.pdf`
4. If no documents indexed: show a warning instead of querying

### Demo mode (`--demo <vertical>`)

- Accepted values: `legal`, `industrial`
- On startup, reads all PDFs/TXTs from `demo/<vertical>/`
- Ingests them into the existing ChromaDB collection (same as normal uploads)
- Reads `demo/<vertical>/preguntas.txt` and displays numbered list
- User can type the number (e.g., `1`) as a shortcut to send that question

### Error handling

- File not found on `/upload`: print error, do not crash
- Empty question: ignore, re-prompt
- LLM/engine error: print error message, do not crash
- `Ctrl+C`: print `Goodbye.` and exit cleanly

---

## Web UI (`web.py`)

### Layout

Two-column Gradio `Blocks` layout:
- **Left column:** file upload component + list of indexed documents (refreshed after each upload)
- **Right column:** `gr.Chatbot` component showing conversation history

Below both columns: text input + submit button.

### Demo mode panel

When launched with `--demo legal` or `--demo industrial`, a `gr.Row` appears at the top with clickable example buttons (one per question in `preguntas.txt`). Clicking a button populates the text input.

### Behavior

- Upload: calls `engine.ingest_document()`, refreshes document list, shows success message in chat
- Query: calls `engine.query()`, appends `(user, answer)` pair to chatbot history, appends `📎 Fuente: <filename>` line after the answer
- No document indexed: returns a warning message in the chat instead of querying

### Deployment

- Local: `python web.py` → `http://localhost:7860`
- Remote: `python web.py --share` → public Gradio URL (temporary, for demos)
- Railway deploy: `web.py` is the entry point, `PORT` env var respected via `server_port`

---

## Demo Content

### `demo/legal/preguntas.txt`
```
¿Cuál es el plazo del contrato?
¿Qué pasa si una parte incumple?
¿Cuál es la cláusula de confidencialidad?
¿Cómo se puede terminar el contrato anticipadamente?
¿Cuál es la jurisdicción en caso de disputa?
```

### `demo/industrial/preguntas.txt`
```
¿Qué hago si la máquina muestra un error?
¿Cuál es el procedimiento de mantenimiento preventivo?
¿Qué equipos de protección se requieren?
¿Cómo se calibra el equipo?
¿Cuáles son las especificaciones técnicas del modelo?
```

### `demo/legal/README.txt` and `demo/industrial/README.txt`
Plain text instructions for the consultant: how to add real client documents before the meeting, how to run the demo, how to reset between clients.

---

## Out of scope

- Authentication / multi-tenant
- Analytics dashboard
- WhatsApp or Slack integration
- Per-client isolated vector stores
- Custom branding per client in the web UI
