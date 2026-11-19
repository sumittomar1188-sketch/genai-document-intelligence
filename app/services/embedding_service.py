import math
from typing import Any

import httpx

from app.config import settings


JINA_EMBEDDINGS_URL = "https://api.jina.ai/v1/embeddings"
JINA_EMBEDDINGS_MODEL = "jina-embeddings-v3"


def generate_embeddings(texts: list[str]) -> list[list[float]]:
    """Generate Jina embeddings for a list of text strings."""
    if not texts:
        return []

    if any(not isinstance(text, str) or not text.strip() for text in texts):
        raise ValueError("texts must contain only non-empty strings.")

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
        "task": "retrieval.passage",
        "input": texts,
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
        raise RuntimeError("Jina AI returned an invalid embeddings response.")

    response_items = result["data"]
    if len(response_items) != len(texts):
        raise RuntimeError(
            "Jina AI returned a different number of embeddings than requested."
        )

    embeddings: list[list[float] | None] = [None] * len(texts)
    for item in response_items:
        if not isinstance(item, dict):
            raise RuntimeError("Jina AI returned an invalid embedding item.")

        index = item.get("index")
        vector = item.get("embedding")
        if (
            not isinstance(index, int)
            or isinstance(index, bool)
            or index < 0
            or index >= len(texts)
            or embeddings[index] is not None
        ):
            raise RuntimeError("Jina AI returned invalid embedding indexes.")

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
            raise RuntimeError("Jina AI returned an invalid embedding vector.")

        embeddings[index] = [float(value) for value in vector]

    if any(embedding is None for embedding in embeddings):
        raise RuntimeError("Jina AI did not return an embedding for every input text.")

    return [embedding for embedding in embeddings if embedding is not None]
