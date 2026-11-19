from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.rag_service import answer_question


router = APIRouter()


class QuestionRequest(BaseModel):
    """Request body for asking a question about uploaded documents."""

    question: str


@router.post("/ask")
def ask_question(
    request: QuestionRequest,
) -> dict[str, str | list[dict[str, str | int | None]]]:
    """Return an answer and its document sources."""
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="The question cannot be empty.")

    try:
        return answer_question(request.question)
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Unable to process the question right now.",
        ) from None
