import os


def pytest_configure(config):
    os.environ.setdefault("LLM_PROVIDER", "groq")
    os.environ.setdefault("GROQ_API_KEY", "test-key")
    os.environ.setdefault("DOCUMENTS_DIR", "./test_data/documents")
    os.environ.setdefault("CHROMA_PATH", "./test_data/chroma")
