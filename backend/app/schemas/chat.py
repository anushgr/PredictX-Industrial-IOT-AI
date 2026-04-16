from pydantic import BaseModel, Field
from typing import Any


class ChatQueryRequest(BaseModel):
    message: str = Field(min_length=1, max_length=3000)


class ChatQueryResponse(BaseModel):
    answer: str
    source: str
    context: dict[str, Any]
    status: str
    intent: str
    data: dict[str, Any] | None = None
