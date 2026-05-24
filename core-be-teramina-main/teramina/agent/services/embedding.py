import logging
import os

logger = logging.getLogger("teramina")

EMBEDDING_MODEL = "text-embedding-3-large"
EMBEDDING_DIM = 3072


def get_embedding(text: str) -> list | None:
    """Return a text-embedding-3-large vector for the given text, or None on failure."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        response = client.embeddings.create(model=EMBEDDING_MODEL, input=text[:8000])
        return response.data[0].embedding
    except Exception as exc:
        logger.warning("Embedding generation failed: %s", exc)
        return None
