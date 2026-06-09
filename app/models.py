from typing import List

from pydantic import BaseModel


class QueryRequest(BaseModel):
    question: str


class QueryResponse(BaseModel):
    answer: str
    sources: List[str] = []


class DocumentInfo(BaseModel):
    filename: str
    id: str


class UploadResponse(BaseModel):
    message: str
    filename: str
    chunks_created: int
