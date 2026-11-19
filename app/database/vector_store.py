import math
from pathlib import Path
from typing import Any
from uuid import uuid4

import httpx
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings

from app.config import settings
from app.services.embedding_service import (
    JINA_EMBEDDINGS_MODEL,
    JINA_EMBEDDINGS_URL,
    generate_embeddings,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CHROMA_DB_DIR = PROJECT_ROOT / "chroma_db"
COLLECTION_NAME = "document_chunks"


def _generate_query_embedding(question: str) -> list[float]:
    """Create a Jina query embedding using its retrieval query task."""
    api_key = settings.jina_api_key.strip()
    if not api_key:
        raise RuntimeError("JINA_API_KEY is missing from the application settings.")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    payload = {
        "model": JINA_EMBEDDINGS_MODEL,
        "task": "retrieval.query",
        "input": [question],
    }

    try:
        response = httpx.post(
            JINA_EMBEDDINGS_URL,
            headers=headers,
            json=payload,
            timeout=30.0,
        )
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise RuntimeError(
            f"Jina AI returned HTTP status {exc.response.status_code}."
        ) from exc
    except httpx.RequestError as exc:
        raise RuntimeError("Could not connect to the Jina AI embeddings API.") from exc

    try:
        result: Any = response.json()
    except ValueError as exc:
        raise RuntimeError("Jina AI returned an invalid JSON response.") from exc

    if not isinstance(result, dict) or not isinstance(result.get("data"), list):
        raise RuntimeError("Jina AI returned an invalid query embedding response.")

    data = result["data"]
    if len(data) != 1 or not isinstance(data[0], dict):
        raise RuntimeError("Jina AI returned an invalid query embedding item.")

    index = data[0].get("index")
    if not isinstance(index, int) or isinstance(index, bool) or index != 0:
        raise RuntimeError("Jina AI returned an invalid query embedding item.")

    vector = data[0].get("embedding")
    if (
        not isinstance(vector, list)
        or not vector
        or any(
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(value)
            for value in vector
        )
    ):
        raise RuntimeError("Jina AI returned an invalid query embedding vector.")

    return [float(value) for value in vector]


class JinaEmbeddings(Embeddings):
    """Use the Jina passage task for documents and query task for questions."""

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return generate_embeddings(texts)

    def embed_query(self, text: str) -> list[float]:
        if not isinstance(text, str) or not text.strip():
            raise ValueError("The search question must be a non-empty string.")
        return _generate_query_embedding(text)


def _get_vector_store() -> Chroma:
    """Open the same persistent Chroma collection for each operation."""
    CHROMA_DB_DIR.mkdir(parents=True, exist_ok=True)
    return Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=JinaEmbeddings(),
        persist_directory=str(CHROMA_DB_DIR),
    )


def add_documents(documents: list[Document]) -> list[str]:
    """Embed and persist document chunks, returning their stored IDs."""
    if not isinstance(documents, list):
        raise TypeError("documents must be a list of LangChain Document objects.")
    if not documents:
        return []

    for document in documents:
        if not isinstance(document, Document):
            raise TypeError("Each item must be a LangChain Document object.")
        if not document.page_content.strip():
            raise ValueError("Document chunks cannot have empty page_content.")

    ids = [str(uuid4()) for _ in documents]
    vector_store = _get_vector_store()
    return vector_store.add_documents(documents=documents, ids=ids)


def search_documents(question: str) -> list[Document]:
    """Return the three most relevant stored chunks for a question."""
    if not isinstance(question, str) or not question.strip():
        raise ValueError("The search question must be a non-empty string.")

    vector_store = _get_vector_store()
    if vector_store._collection.count() == 0:
        return []

    return vector_store.similarity_search(query=question, k=3)
