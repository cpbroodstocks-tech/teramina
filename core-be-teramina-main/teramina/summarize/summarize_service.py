# pylint: disable=E0401
"""single chat services is service for chat but without any memory"""

import os
import time
import logging
from langchain.vectorstores.pinecone import Pinecone
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.agents import AgentExecutor
from langchain.agents.openai_functions_agent.base import OpenAIFunctionsAgent
from langchain.chat_models import ChatOpenAI, ChatAnyscale
from langchain.agents.agent_toolkits import create_retriever_tool
import pinecone

from teramina.summarize.prompt_service import Prompt

logger = logging.getLogger(__name__)

MAX_QUESTION_LENGTH = 2000
_MAX_RETRIES = 3

pinecone_api_key = os.getenv("PINECONE_API_KEY")
pinecone_env = os.getenv("PINECONE_ENV")
pinecone_index = os.getenv("PINECONE_INDEX")

pinecone.init(api_key=pinecone_api_key, environment=pinecone_env)


class SingleChat:
    """SingleChat Service"""

    def __init__(self, model):
        open_api_key = os.getenv("open_ai_key")
        embedding = OpenAIEmbeddings(openai_api_key=open_api_key)
        if model == "openai":
            llm = ChatOpenAI(
                openai_api_key=os.getenv("open_ai_key"),
                model_name="gpt-4-1106-preview",
                temperature=0.6,
                max_tokens=1500,
            )
        else:
            llm = ChatAnyscale(
                anyscale_api_key=os.getenv("anyscale_api_key"),
                model="mistralai/Mixtral-8x7B-Instruct-v0.1",
                temperature=0.1,
            )

        self.embeddings = embedding
        self.llm = llm
        self.model = model

    def generate_retrieval_tool(self):
        """generate retrieval tool"""
        # retrieve vector db from pinecone
        index = pinecone.Index(pinecone_index)
        vectorstore = Pinecone(index, self.embeddings, "text", namespace="default")
        retriever = vectorstore.as_retriever()

        # generate tool
        retrieve_tool = create_retriever_tool(
            retriever,
            "search_relevant_documents",  # function name
            "Searches and returns documents regarding based on the query.",
        )
        return retrieve_tool

    def _build_executor(self, language):
        prompt = Prompt.prompt_report(language)
        tools = [self.generate_retrieval_tool()]
        agent = OpenAIFunctionsAgent(llm=self.llm, tools=tools, prompt=prompt)
        return AgentExecutor(
            agent=agent,
            tools=tools,
            verbose=False,
            max_iterations=2,
            early_stopping_method="generate",
            return_intermediate_steps=False,
        )

    def ask(self, question: str, language: str = None):
        """ask a question"""
        if len(question) > MAX_QUESTION_LENGTH:
            question = question[:MAX_QUESTION_LENGTH]

        agent_executor = self._build_executor(language)
        last_exc = None
        for attempt in range(_MAX_RETRIES):
            try:
                return agent_executor({"input": question})
            except Exception as exc:  # pylint: disable=broad-except
                last_exc = exc
                if attempt < _MAX_RETRIES - 1:
                    time.sleep(2 ** attempt)
                    logger.warning("OpenAI retry %d: %s", attempt + 1, exc)
        logger.error("OpenAI ask failed after %d retries: %s", _MAX_RETRIES, last_exc)
        return None

    async def stream_ask(self, question: str, language: str = None):
        """ask a question"""
        if len(question) > MAX_QUESTION_LENGTH:
            question = question[:MAX_QUESTION_LENGTH]

        agent_executor = self._build_executor(language)
        try:
            return await agent_executor.arun(question)
        except Exception as exc:  # pylint: disable=broad-except
            logger.error("OpenAI stream_ask failed: %s", exc)
            return None
