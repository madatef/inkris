from langchain_openai import ChatOpenAI

from app.config import settings

def orchestrator_llm() -> ChatOpenAI:
    return ChatOpenAI(model=settings.ORCHESTRATOR_OPENAI_MODEL, temperature=0.2, api_key=settings.OPENAI_API_KEY)


def rag_llm() -> ChatOpenAI:
    # Slightly lower creativity for exactness and factual responses
    return ChatOpenAI(model=settings.RAG_OPENAI_MODEL, temperature=0.0, api_key=settings.OPENAI_API_KEY)

def summarization_llm() -> ChatOpenAI:
    return ChatOpenAI(model=settings.SUMMARIZATION_OPENAI_MODEL, temperature=0.0, api_key=settings.OPENAI_API_KEY)