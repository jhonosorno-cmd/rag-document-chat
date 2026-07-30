from unittest.mock import MagicMock, patch

import pytest

from app.rag_engine import RAGEngine


class TestRAGEngineQuery:
    def test_query_returns_answer_and_sources(self):
        with patch("app.rag_engine.Groq"), \
             patch("app.rag_engine.Anthropic"), \
             patch("app.rag_engine.HuggingFaceEmbedding"), \
             patch("app.rag_engine.Settings"), \
             patch("app.rag_engine.chromadb.PersistentClient") as mock_chroma, \
             patch("app.rag_engine.ChromaVectorStore"), \
             patch("app.rag_engine.VectorStoreIndex") as mock_index_cls, \
             patch("app.rag_engine.StorageContext"):

            mock_chroma.return_value.get_or_create_collection.return_value = MagicMock()

            mock_response = MagicMock()
            mock_response.__str__ = lambda self: "El contrato vence en 2025."
            node = MagicMock()
            node.metadata = {"file_name": "contrato.pdf"}
            mock_response.source_nodes = [node]

            mock_qe = MagicMock()
            mock_qe.query.return_value = mock_response
            mock_index = MagicMock()
            mock_index.as_query_engine.return_value = mock_qe
            mock_index_cls.from_vector_store.return_value = mock_index

            engine = RAGEngine()
            result = engine.query("¿Cuándo vence?")

            assert result["answer"] == "El contrato vence en 2025."
            assert result["sources"] == ["contrato.pdf"]

    def test_query_deduplicates_sources(self):
        with patch("app.rag_engine.Groq"), \
             patch("app.rag_engine.Anthropic"), \
             patch("app.rag_engine.HuggingFaceEmbedding"), \
             patch("app.rag_engine.Settings"), \
             patch("app.rag_engine.chromadb.PersistentClient") as mock_chroma, \
             patch("app.rag_engine.ChromaVectorStore"), \
             patch("app.rag_engine.VectorStoreIndex") as mock_index_cls, \
             patch("app.rag_engine.StorageContext"):

            mock_chroma.return_value.get_or_create_collection.return_value = MagicMock()

            mock_response = MagicMock()
            mock_response.__str__ = lambda self: "answer"
            node1, node2 = MagicMock(), MagicMock()
            node1.metadata = {"file_name": "doc.pdf"}
            node2.metadata = {"file_name": "doc.pdf"}
            mock_response.source_nodes = [node1, node2]

            mock_qe = MagicMock()
            mock_qe.query.return_value = mock_response
            mock_index = MagicMock()
            mock_index.as_query_engine.return_value = mock_qe
            mock_index_cls.from_vector_store.return_value = mock_index

            engine = RAGEngine()
            result = engine.query("question")

            assert result["sources"] == ["doc.pdf"]


class TestRAGEngineIngest:
    def test_ingest_returns_chunk_count(self):
        with patch("app.rag_engine.Groq"), \
             patch("app.rag_engine.Anthropic"), \
             patch("app.rag_engine.HuggingFaceEmbedding"), \
             patch("app.rag_engine.Settings"), \
             patch("app.rag_engine.chromadb.PersistentClient") as mock_chroma, \
             patch("app.rag_engine.ChromaVectorStore"), \
             patch("app.rag_engine.VectorStoreIndex") as mock_index_cls, \
             patch("app.rag_engine.StorageContext"), \
             patch("app.rag_engine.fitz") as mock_fitz, \
             patch("app.rag_engine.SentenceSplitter") as mock_splitter:

            mock_chroma.return_value.get_or_create_collection.return_value = MagicMock()
            mock_index = MagicMock()
            mock_index_cls.from_vector_store.return_value = mock_index

            mock_page = MagicMock()
            mock_page.get_text.return_value = "some text"
            mock_pdf = MagicMock()
            mock_pdf.__iter__.return_value = iter([mock_page])
            mock_fitz.open.return_value = mock_pdf

            mock_splitter.return_value.get_nodes_from_documents.return_value = [
                MagicMock(), MagicMock(), MagicMock()
            ]

            engine = RAGEngine()
            count = engine.ingest_document("./data/documents/test.pdf")

            assert count == 3
            mock_index.insert_nodes.assert_called_once()


class TestRAGEngineListDocuments:
    def test_list_returns_unique_filenames(self):
        with patch("app.rag_engine.Groq"), \
             patch("app.rag_engine.Anthropic"), \
             patch("app.rag_engine.HuggingFaceEmbedding"), \
             patch("app.rag_engine.Settings"), \
             patch("app.rag_engine.chromadb.PersistentClient") as mock_chroma, \
             patch("app.rag_engine.ChromaVectorStore"), \
             patch("app.rag_engine.VectorStoreIndex") as mock_index_cls, \
             patch("app.rag_engine.StorageContext"):

            mock_collection = MagicMock()
            mock_collection.get.return_value = {
                "ids": ["1", "2", "3"],
                "metadatas": [
                    {"file_name": "a.pdf"},
                    {"file_name": "b.txt"},
                    {"file_name": "a.pdf"},
                ],
            }
            mock_chroma.return_value.get_or_create_collection.return_value = mock_collection
            mock_index_cls.from_vector_store.return_value = MagicMock()

            engine = RAGEngine()
            docs = engine.list_documents()

            assert sorted(docs) == ["a.pdf", "b.txt"]


class TestRAGEngineDelete:
    def test_delete_existing_document_returns_true(self):
        with patch("app.rag_engine.Groq"), \
             patch("app.rag_engine.Anthropic"), \
             patch("app.rag_engine.HuggingFaceEmbedding"), \
             patch("app.rag_engine.Settings"), \
             patch("app.rag_engine.chromadb.PersistentClient") as mock_chroma, \
             patch("app.rag_engine.ChromaVectorStore"), \
             patch("app.rag_engine.VectorStoreIndex") as mock_index_cls, \
             patch("app.rag_engine.StorageContext"):

            mock_collection = MagicMock()
            mock_collection.get.return_value = {
                "ids": ["chunk1", "chunk2"],
                "metadatas": [{"file_name": "target.pdf"}, {"file_name": "other.pdf"}],
            }
            mock_chroma.return_value.get_or_create_collection.return_value = mock_collection
            mock_index_cls.from_vector_store.return_value = MagicMock()

            engine = RAGEngine()
            result = engine.delete_document("target.pdf")

            assert result is True
            mock_collection.delete.assert_called_once_with(ids=["chunk1"])

    def test_delete_missing_document_returns_false(self):
        with patch("app.rag_engine.Groq"), \
             patch("app.rag_engine.Anthropic"), \
             patch("app.rag_engine.HuggingFaceEmbedding"), \
             patch("app.rag_engine.Settings"), \
             patch("app.rag_engine.chromadb.PersistentClient") as mock_chroma, \
             patch("app.rag_engine.ChromaVectorStore"), \
             patch("app.rag_engine.VectorStoreIndex") as mock_index_cls, \
             patch("app.rag_engine.StorageContext"):

            mock_collection = MagicMock()
            mock_collection.get.return_value = {
                "ids": ["1"],
                "metadatas": [{"file_name": "other.pdf"}],
            }
            mock_chroma.return_value.get_or_create_collection.return_value = mock_collection
            mock_index_cls.from_vector_store.return_value = MagicMock()

            engine = RAGEngine()
            result = engine.delete_document("ghost.pdf")

            assert result is False
            mock_collection.delete.assert_not_called()
