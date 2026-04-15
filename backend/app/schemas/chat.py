from pydantic import BaseModel, Field


class ChatQueryRequest(BaseModel):
    message: str = Field(min_length=1, max_length=3000)


class ChatQueryResponse(BaseModel):
    answer: str
    source: str
    context: dict
