from __future__ import annotations

import os
from functools import lru_cache
from typing import List, TypedDict

from typing_extensions import Literal

from langchain import hub
from langchain.chat_models import ChatOpenAI
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores.pgvector import PGVector
from langchain_core.documents import Document
from langgraph.graph import START, END, StateGraph

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PG_CONN = (
    f"postgresql+psycopg://{os.getenv('PG_USER')}:{os.getenv('PG_PASSWORD')}"
    f"@{os.getenv('PG_HOST', 'db')}:{os.getenv('PG_PORT', '5432')}/{os.getenv('PG_DATABASE')}"
)
PG_COLLECTION = os.getenv("PG_COLLECTION", "hipaa_chunks")

EMBEDDINGS = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)
LLM = ChatOpenAI(model="gpt-4o", temperature=0, openai_api_key=OPENAI_API_KEY)
PROMPT = hub.pull("rlm/rag-prompt")

@lru_cache(maxsize=1)
def store() -> PGVector:
    return PGVector(
        collection_name=PG_COLLECTION,
        connection_string=PG_CONN,
        embedding_function=EMBEDDINGS,
    )


class State(TypedDict):
    question: str
    context: List[Document]
    answer: str
    decision: Literal["yes", "no"]


def decide(state: State) -> dict:
    """
    LLM принимает решение: нужна ли внешняя информация
    """
    system = (
        "Ты решаешь, нужна ли внешняя контекстная информация, "
        "чтобы ответить на вопрос пользователя. "
        "Ответь ровно 'yes' или 'no'."
    )
    msg = [{"role": "system", "content": system},
           {"role": "user", "content": state["question"]}]
    decision = LLM.invoke(msg).content.strip().lower()
    decision = "yes" if "yes" in decision else "no"
    return {"decision": decision}


def retrieve(state: State) -> dict:
    docs = store().similarity_search(state["question"], k=8)
    return {"context": docs}


def generate(state: State) -> dict:
    docs_text = "\n\n".join(d.page_content for d in state.get("context", []))
    prompt_msg = PROMPT.invoke({"question": state["question"], "context": docs_text})
    response = LLM.invoke(prompt_msg).content
    return {"answer": response}


graph_builder = StateGraph(State)

graph_builder.add_node("decide", decide)
graph_builder.add_node("retrieve", retrieve)
graph_builder.add_node("generate", generate)

graph_builder.add_edge(START, "decide")
graph_builder.add_conditional_edges(
    "decide",
    lambda s: s["decision"],
    {
        "yes": "retrieve",
        "no": "generate",
    },
)
graph_builder.add_edge("retrieve", "generate")
graph_builder.add_edge("generate", END)

GRAPH = graph_builder.compile()


def answer(question: str) -> dict:
    result = GRAPH.invoke({"question": question})
    print(result)
    return {
        "answer": result["answer"],
        "sources": [
            {"page_content": d.page_content, "metadata": d.metadata}
            for d in result.get("context", [])
        ],
        "used_retrieval": result["decision"] == "yes",
    }
