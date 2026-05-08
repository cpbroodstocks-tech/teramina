# pylint: disable=E0401
"""SingleChat service — direct Anthropic Claude integration with Pinecone RAG."""

import os
import time
import logging
import anthropic

from teramina.summarize.prompt_service import Prompt

logger = logging.getLogger(__name__)

MAX_QUESTION_LENGTH = 2000
_MAX_RETRIES = 3

_PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
_PINECONE_INDEX = os.getenv("PINECONE_INDEX")
_OPENAI_KEY = os.getenv("open_ai_key")
_ANTHROPIC_KEY = os.getenv("ANTHROPIC_API_KEY")


class SingleChat:
    """SingleChat Service"""

    def __init__(self, model=None):
        # model param kept for call-site compatibility; only Claude is used
        self.client = anthropic.Anthropic(api_key=_ANTHROPIC_KEY)
        self.async_client = anthropic.AsyncAnthropic(api_key=_ANTHROPIC_KEY)
        self.model_id = "claude-sonnet-4-6"

    def _get_context(self, question: str, namespace: str = "default") -> str:
        """Query Pinecone for relevant context documents."""
        try:
            import openai
            from pinecone import Pinecone as PineconeClient

            oc = openai.OpenAI(api_key=_OPENAI_KEY)
            embedding = oc.embeddings.create(
                input=question, model="text-embedding-ada-002"
            ).data[0].embedding

            index = PineconeClient(api_key=_PINECONE_API_KEY).Index(_PINECONE_INDEX)
            results = index.query(
                vector=embedding, top_k=4, namespace=namespace, include_metadata=True
            )
            docs = [m.metadata.get("text", "") for m in results.matches if m.metadata]
            return "\n\n".join(docs) if docs else ""
        except Exception as exc:  # pylint: disable=broad-except
            logger.warning("Context retrieval failed: %s", exc)
            return ""

    def ask(self, question: str, language: str = None) -> dict | None:
        """ask a question (synchronous)"""
        if len(question) > MAX_QUESTION_LENGTH:
            question = question[:MAX_QUESTION_LENGTH]

        language = language or "english"
        context = self._get_context(question)
        system_prompt = Prompt.prompt_report(language, context)

        last_exc = None
        for attempt in range(_MAX_RETRIES):
            try:
                response = self.client.messages.create(
                    model=self.model_id,
                    max_tokens=1500,
                    system=system_prompt,
                    messages=[{"role": "user", "content": question}],
                )
                return {"output": response.content[0].text}
            except Exception as exc:  # pylint: disable=broad-except
                last_exc = exc
                if attempt < _MAX_RETRIES - 1:
                    time.sleep(2 ** attempt)
                    logger.warning("Anthropic retry %d: %s", attempt + 1, exc)
        logger.error("Anthropic ask failed after %d retries: %s", _MAX_RETRIES, last_exc)
        return None

    async def stream_ask(self, question: str, language: str = None) -> str | None:
        """ask a question (async)"""
        if len(question) > MAX_QUESTION_LENGTH:
            question = question[:MAX_QUESTION_LENGTH]

        language = language or "english"
        context = self._get_context(question)
        system_prompt = Prompt.prompt_report(language, context)

        try:
            response = await self.async_client.messages.create(
                model=self.model_id,
                max_tokens=1500,
                system=system_prompt,
                messages=[{"role": "user", "content": question}],
            )
            return response.content[0].text
        except Exception as exc:  # pylint: disable=broad-except
            logger.error("Anthropic stream_ask failed: %s", exc)
            return None
