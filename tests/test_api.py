import io

import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch


@pytest.fixture
def client():
    with patch("app.main.RAGEngine") as mock_cls:
        mock_rag = MagicMock()
        mock_cls.return_value = mock_rag
        from app.main import app
        with TestClient(app) as c:
            yield c, mock_rag


def test_upload_pdf_returns_chunk_count(client):
    c, mock_rag = client
    mock_rag.ingest_document.return_value = 7

    response = c.post(
        "/upload",
        files={"file": ("contract.pdf", io.BytesIO(b"%PDF fake"), "application/pdf")},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["filename"] == "contract.pdf"
    assert body["chunks_created"] == 7
    assert "indexed" in body["message"].lower()


def test_upload_txt_is_accepted(client):
    c, mock_rag = client
    mock_rag.ingest_document.return_value = 3

    response = c.post(
        "/upload",
        files={"file": ("notes.txt", io.BytesIO(b"hello world"), "text/plain")},
    )

    assert response.status_code == 200


def test_upload_unsupported_extension_returns_400(client):
    c, mock_rag = client

    response = c.post(
        "/upload",
        files={"file": ("report.docx", io.BytesIO(b"fake"), "application/octet-stream")},
    )

    assert response.status_code == 400


def test_query_returns_answer_and_sources(client):
    c, mock_rag = client
    mock_rag.query.return_value = {
        "answer": "El plazo es 30 días.",
        "sources": ["contrato.pdf"],
    }

    response = c.post("/query", json={"question": "¿Cuál es el plazo?"})

    assert response.status_code == 200
    body = response.json()
    assert body["answer"] == "El plazo es 30 días."
    assert body["sources"] == ["contrato.pdf"]


def test_query_requires_question_field(client):
    c, mock_rag = client

    response = c.post("/query", json={})

    assert response.status_code == 422


def test_list_documents_returns_all(client):
    c, mock_rag = client
    mock_rag.list_documents.return_value = ["manual.pdf", "contrato.txt"]

    response = c.get("/documents")

    assert response.status_code == 200
    docs = response.json()
    assert len(docs) == 2
    filenames = [d["filename"] for d in docs]
    assert "manual.pdf" in filenames
    assert "contrato.txt" in filenames


def test_delete_existing_document(client):
    c, mock_rag = client
    mock_rag.delete_document.return_value = True

    response = c.delete("/documents/manual.pdf")

    assert response.status_code == 200
    mock_rag.delete_document.assert_called_once_with("manual.pdf")


def test_delete_nonexistent_document_returns_404(client):
    c, mock_rag = client
    mock_rag.delete_document.return_value = False

    response = c.delete("/documents/ghost.pdf")

    assert response.status_code == 404


def test_upload_with_path_traversal_filename_is_sanitized(client):
    c, mock_rag = client
    mock_rag.ingest_document.return_value = 2

    response = c.post(
        "/upload",
        files={"file": ("../evil.pdf", io.BytesIO(b"%PDF fake"), "application/pdf")},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["filename"] == "evil.pdf"
