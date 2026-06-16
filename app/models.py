from pydantic import BaseModel


class QueryRequest(BaseModel):
    question: str
    chat_history: list[dict] = []


class QueryResponse(BaseModel):
    answer: str
    sources: list[str] = []


class DocumentInfo(BaseModel):
    filename: str


class UploadResponse(BaseModel):
    message: str
    filename: str
    chunks_created: int
