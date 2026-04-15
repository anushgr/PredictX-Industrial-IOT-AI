from fastapi import APIRouter, Depends

from app.dependencies import get_current_user
from app.schemas.chat import ChatQueryRequest, ChatQueryResponse
from app.services.chatbot_engine import answer_question
from app.services.nim_chat import build_realtime_context, query_nim_chat

router = APIRouter()


@router.post("/chat/query", response_model=ChatQueryResponse)
def chat_query(payload: ChatQueryRequest, _: dict = Depends(get_current_user)) -> ChatQueryResponse:
    # Try database-driven Q&A first
    db_result = answer_question(payload.message)
    answer = db_result.get("answer", "")
    source = "database"
    context = db_result.get("context", "Database Q&A")
    
    # If user has NIM configured and no clear DB answer, try NIM for richer insights
    if not answer or db_result.get("status") == "error":
        realtime_context = build_realtime_context()
        answer, source = query_nim_chat(payload.message, realtime_context)
        context = realtime_context
    
    return ChatQueryResponse(answer=answer, source=source, context=context)
