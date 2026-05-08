# pylint: disable=no-member, no-name-in-module, too-many-locals

import os
import uuid
import dotenv
import pandas as pd
from pinecone import Pinecone as PineconeClient
import openai

dotenv.load_dotenv()

_OPENAI_KEY = os.getenv("open_ai_key")
_PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
_PINECONE_INDEX = os.getenv("PINECONE_INDEX")

_EMBED_MODEL = "text-embedding-ada-002"
_BATCH_SIZE = 100


class PineconeIndexing:
    """Pinecone indexing — direct SDK, no LangChain."""

    def __init__(self, user_id: str):
        self.user_id = str(user_id)
        self.index = PineconeClient(api_key=_PINECONE_API_KEY).Index(_PINECONE_INDEX)
        self.oc = openai.OpenAI(api_key=_OPENAI_KEY)

    def _embed(self, texts: list) -> list:
        response = self.oc.embeddings.create(input=texts, model=_EMBED_MODEL)
        return [d.embedding for d in response.data]

    def _document_generator(self, df: pd.DataFrame) -> list:
        df = df.copy()
        df["date"] = df["date"].astype(str)
        df["content"] = df.apply(lambda r: str(r.to_dict()), axis=1)
        return df[["date", "doc", "cycle_name", "pond_name", "farm_name", "content"]].to_dict("records")

    def create_index(self, df: pd.DataFrame) -> list:
        """Embed and upsert documents; return list of vector IDs."""
        records = self._document_generator(df)
        texts = [r["content"] for r in records]
        embeddings = self._embed(texts)

        vectors = [
            {
                "id": str(uuid.uuid4()),
                "values": emb,
                "metadata": {"text": rec["content"], **{k: rec[k] for k in ("date", "doc", "cycle_name", "pond_name", "farm_name")}},
            }
            for rec, emb in zip(records, embeddings)
        ]

        ids = []
        for i in range(0, len(vectors), _BATCH_SIZE):
            batch = vectors[i : i + _BATCH_SIZE]
            self.index.upsert(vectors=batch, namespace=self.user_id)
            ids.extend(v["id"] for v in batch)
        return ids

    def delete_index(self, ids: list) -> None:
        """Delete vectors by ID from this user's namespace."""
        if ids:
            self.index.delete(ids=ids, namespace=self.user_id)

    def update_index(self, ids: list, df: pd.DataFrame) -> list:
        """Delete old vectors, create new ones, return new IDs."""
        self.delete_index(ids)
        return self.create_index(df)
