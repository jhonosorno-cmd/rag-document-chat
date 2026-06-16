import chromadb
import fitz
from itertools import zip_longest
from pathlib import Path
from llama_index.core import SimpleDirectoryReader, StorageContext, VectorStoreIndex
from llama_index.core import Settings
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.prompts import PromptTemplate
from llama_index.core.schema import Document
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.anthropic import Anthropic
from llama_index.llms.groq import Groq
from llama_index.vector_stores.chroma import ChromaVectorStore

from app.config import settings as cfg

_QA_TEMPLATE = PromptTemplate(
    "Eres un asistente experto que responde preguntas basándose exclusivamente en el contenido del documento.\n"
    "Instrucciones:\n"
    "- Proporciona la información real del documento, no solo referencias a otras secciones.\n"
    "- Si el contexto menciona que el contenido está en otra parte, usa lo que sí está disponible en el contexto.\n"
    "- Responde siempre en el mismo idioma de la pregunta.\n"
    "- Si la información no está en el contexto, respondé: 'No encontré esa información en el documento.'\n\n"
    "Contexto del documento:\n"
    "---------------------\n"
    "{context_str}\n"       
    "---------------------\n"
    "Pregunta: {query_str}\n"
    "Respuesta:"
)


class RAGEngine:
    def __init__(self):
        self._setup_llm()
        self._setup_embeddings()
        self._setup_vector_store()
        self.index = self._load_index()

    def _setup_llm(self):
        if cfg.llm_provider == "anthropic":
            Settings.llm = Anthropic(model=cfg.anthropic_model, api_key=cfg.anthropic_api_key)
        else:
            Settings.llm = Groq(model=cfg.groq_model, api_key=cfg.groq_api_key)

    def _setup_embeddings(self):
        is_e5 = "e5" in cfg.embedding_model.lower()
        Settings.embed_model = HuggingFaceEmbedding(
            model_name=cfg.embedding_model,
            query_instruction="query: " if is_e5 else None,
            text_instruction="passage: " if is_e5 else None,
        )
        Settings.chunk_size = cfg.chunk_size
        Settings.chunk_overlap = cfg.chunk_overlap

    def _setup_vector_store(self):
        self.chroma_client = chromadb.PersistentClient(path=cfg.chroma_path)
        self.collection = self.chroma_client.get_or_create_collection("documents")
        self.vector_store = ChromaVectorStore(chroma_collection=self.collection)

    def _load_index(self) -> VectorStoreIndex:
        storage_context = StorageContext.from_defaults(vector_store=self.vector_store)
        return VectorStoreIndex.from_vector_store(self.vector_store, storage_context=storage_context)

    def _load_documents(self, file_path: str):
        if Path(file_path).suffix.lower() == ".pdf":
            pdf = fitz.open(file_path)
            docs = [
                Document(
                    text=page.get_text(),
                    metadata={"file_name": Path(file_path).name, "page_label": str(i + 1)},
                )
                for i, page in enumerate(pdf)
                if page.get_text().strip()
            ]
            pdf.close()
            return docs
        return SimpleDirectoryReader(input_files=[file_path]).load_data()

    def ingest_document(self, file_path: str) -> int:
        filename = Path(file_path).name
        self.delete_document(filename)
        docs = self._load_documents(file_path)
        splitter = SentenceSplitter(chunk_size=cfg.chunk_size, chunk_overlap=cfg.chunk_overlap)
        nodes = splitter.get_nodes_from_documents(docs)
        self.index.insert_nodes(nodes)
        return len(nodes)

    def _standalone_question(self, question: str, chat_history: list) -> str:
        recent = chat_history[-6:]
        lines = []
        for m in recent:
            role = "Usuario" if m["role"] == "user" else "Asistente"
            content = str(m.get("content", "")).split("\n\n📎")[0]
            lines.append(f"{role}: {content}")
        prompt = (
            f"Historial de conversación:\n{chr(10).join(lines)}\n\n"
            f"Pregunta de seguimiento: {question}\n\n"
            "Reformulá la pregunta de seguimiento como una pregunta independiente y completa "
            "que no requiera el historial para ser entendida. "
            "Respondé solo con la pregunta reformulada, sin explicaciones."
        )
        try:
            return str(Settings.llm.complete(prompt)).strip() or question
        except Exception:
            return question

    def query(self, question: str, chat_history: list = None) -> dict:
        if chat_history:
            question = self._standalone_question(question, chat_history)
        engine = self.index.as_query_engine(
            similarity_top_k=cfg.top_k_results,
            text_qa_template=_QA_TEMPLATE,
        )
        response = engine.query(question)
        sources = list({
            node.metadata["file_name"]
            for node in response.source_nodes
            if "file_name" in node.metadata
        })
        return {"answer": str(response), "sources": sources}

    def list_documents(self) -> list:
        results = self.collection.get(include=["metadatas"])
        filenames = {
            meta["file_name"]
            for meta in results.get("metadatas", [])
            if meta and "file_name" in meta
        }
        return list(filenames)

    def delete_document(self, filename: str) -> bool:
        results = self.collection.get(include=["metadatas"])
        ids_to_delete = [
            id_
            for id_, meta in zip_longest(results["ids"], results["metadatas"])
            if meta and meta.get("file_name") == filename
        ]
        if not ids_to_delete:
            return False
        self.collection.delete(ids=ids_to_delete)
        return True
