import chromadb
from itertools import zip_longest
from llama_index.core import SimpleDirectoryReader, StorageContext, VectorStoreIndex
from llama_index.core import Settings
from llama_index.core.node_parser import SentenceSplitter
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.anthropic import Anthropic
from llama_index.llms.groq import Groq
from llama_index.vector_stores.chroma import ChromaVectorStore

from app.config import settings as cfg


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
        Settings.embed_model = HuggingFaceEmbedding(model_name=cfg.embedding_model)
        Settings.chunk_size = cfg.chunk_size
        Settings.chunk_overlap = cfg.chunk_overlap

    def _setup_vector_store(self):
        self.chroma_client = chromadb.PersistentClient(path=cfg.chroma_path)
        self.collection = self.chroma_client.get_or_create_collection("documents")
        self.vector_store = ChromaVectorStore(chroma_collection=self.collection)

    def _load_index(self) -> VectorStoreIndex:
        storage_context = StorageContext.from_defaults(vector_store=self.vector_store)
        return VectorStoreIndex.from_vector_store(self.vector_store, storage_context=storage_context)

    def ingest_document(self, file_path: str) -> int:
        docs = SimpleDirectoryReader(input_files=[file_path]).load_data()
        splitter = SentenceSplitter(chunk_size=cfg.chunk_size, chunk_overlap=cfg.chunk_overlap)
        nodes = splitter.get_nodes_from_documents(docs)
        self.index.insert_nodes(nodes)
        return len(nodes)

    def query(self, question: str) -> dict:
        engine = self.index.as_query_engine(similarity_top_k=cfg.top_k_results)
        response = engine.query(question)
        sources = list({
            node.metadata["file_name"]
            for node in response.source_nodes
            if "file_name" in node.metadata
        })
        return {"answer": str(response), "sources": sources}

    def list_documents(self) -> list:
        results = self.collection.get()
        filenames = {
            meta["file_name"]
            for meta in results.get("metadatas", [])
            if meta and "file_name" in meta
        }
        return list(filenames)

    def delete_document(self, filename: str) -> bool:
        results = self.collection.get()
        ids_to_delete = [
            id_
            for id_, meta in zip_longest(results["ids"], results["metadatas"])
            if meta and meta.get("file_name") == filename
        ]
        if not ids_to_delete:
            return False
        self.collection.delete(ids=ids_to_delete)
        return True
