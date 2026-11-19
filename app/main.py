from fastapi import FastAPI

from app.routes.documents import router as documents_router
from app.routes.questions import router as questions_router


app = FastAPI(
    title="Document Q&A Assistant",
    description=(
        "Upload documents and ask questions about their content using "
        "retrieval-augmented generation (RAG)."
    ),
)

app.include_router(documents_router, prefix="/documents")
app.include_router(questions_router, prefix="/questions")


@app.get("/health")
def health_check() -> dict[str, str]:
    """Return the current health status of the API."""
    return {
        "status": "healthy",
        "message": "Document Q&A Assistant API is running",
    }
