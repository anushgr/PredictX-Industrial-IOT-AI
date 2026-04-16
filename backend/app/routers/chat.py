from fastapi import APIRouter

from app.schemas.chat import ChatQueryRequest, ChatQueryResponse
from app.services.chatbot_engine import answer_question

router = APIRouter()


@router.post("/chat/query", response_model=ChatQueryResponse)
def chat_query(payload: ChatQueryRequest) -> ChatQueryResponse:
    db_result = answer_question(payload.message)

    return ChatQueryResponse(
        answer=str(db_result.get("answer", "No response generated from database.")),
        source="database",
        context=db_result.get("context", {}),
        status=str(db_result.get("status", "error")),
        intent=str(db_result.get("intent", "summary")),
        data=db_result.get("data"),
    )
