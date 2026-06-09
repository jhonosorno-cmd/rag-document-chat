from contextlib import asynccontextmanager
from pathlib import Path
import shutil

from fastapi import FastAPI, File, HTTPException, Request, UploadFile

from app.config import settings
from app.models import DocumentInfo, QueryRequest, QueryResponse, UploadResponse
from app.rag_engine import RAGEngine

_ALLOWED_EXTENSIONS = {".pdf", ".txt"}


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.rag = RAGEngine()
    yield


app = FastAPI(title="RAG Document Chat", version="1.0.0", lifespan=lifespan)


@app.post("/upload", response_model=UploadResponse)
async def upload_document(request: Request, file: UploadFile = File(...)):
    ext = Path(file.filename).suffix.lower()
    if ext not in _ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Only {_ALLOWED_EXTENSIONS} files are accepted")

    dest = Path(settings.documents_dir) / file.filename
    dest.parent.mkdir(parents=True, exist_ok=True)
    with dest.open("wb") as f:
        shutil.copyfileobj(file.file, f)

    chunks = request.app.state.rag.ingest_document(str(dest))
    return UploadResponse(message="Document indexed", filename=file.filename, chunks_created=chunks)


@app.post("/query", response_model=QueryResponse)
async def query_documents(request: Request, body: QueryRequest):
    result = request.app.state.rag.query(body.question)
    return QueryResponse(answer=result["answer"], sources=result["sources"])


@app.get("/documents", response_model=list[DocumentInfo])
async def list_documents(request: Request):
    docs = request.app.state.rag.list_documents()
    return [DocumentInfo(filename=d, id=d) for d in docs]


@app.delete("/documents/{filename}")
async def delete_document(request: Request, filename: str):
    deleted = request.app.state.rag.delete_document(filename)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Document '{filename}' not found")
    return {"message": f"Document '{filename}' deleted"}
