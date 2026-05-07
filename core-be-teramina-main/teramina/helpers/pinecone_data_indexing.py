# pylint: disable=no-member, no-name-in-module, too-many-locals

import os
import dotenv
import pandas as pd
from langchain.vectorstores.pinecone import Pinecone
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.document_loaders import DataFrameLoader
import pinecone

dotenv.load_dotenv()

OPENAI_KEY = os.getenv("open_ai_key")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_ENV = os.getenv("PINECONE_ENV")
PINECONE_INDEX = os.getenv("PINECONE_INDEX")

# pinecone initialization
pinecone.init(api_key=PINECONE_API_KEY, environment=PINECONE_ENV)


class PineconeIndexing:
    """Pinecone indexing function"""

    def __init__(self, user_id: str):
        """initialization"""
        self.user_id = user_id
        embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_KEY)
        self.pc = Pinecone(
            index=pinecone.Index(PINECONE_INDEX),
            embedding=embeddings,
            text_key="text",
            namespace=str(user_id),
        )

    def _document_generator(self, df: pd.DataFrame):
        """document prepartion"""
        df["date"] = df["date"].astype(str)
        df["content"] = df.to_dict("records")
        df["content"] = df["content"].astype(str)
        df = df[["date", "doc", "cycle_name", "pond_name", "farm_name", "content"]]
        loader = DataFrameLoader(df, page_content_column="content")
        data = loader.load()
        # text_splitter = RecursiveCharacterTextSplitter(
        #     separators=[", "], chunk_size=1000, chunk_overlap=0
        # )
        # texts = text_splitter.split_documents(data)
        return data

    def create_index(self, df: pd.DataFrame) -> list:
        """create index using pinecone

        df (pd.DataFrame): data that would be updated
        """

        data = self._document_generator(df)
        ids = self.pc.add_documents(data)
        return ids

    def delete_index(self, ids: list):
        """delete vector index from pinecone

        ids (list): vector ids
        """
        self.pc.delete(ids=ids, namespace=str(self.user_id))

    def update_index(self, ids: list, df: pd.DataFrame) -> list:
        """update vector index

        ids (list): vector ids
        df (pd.DataFrame): data that would be updated
        """
        # delete the old index
        self.delete_index(ids)

        # create new index
        new_ids = self.create_index(df)
        return new_ids
