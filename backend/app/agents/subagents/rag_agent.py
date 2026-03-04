from langchain.agents import create_agent

from app.agents.tools.rag_tools import RAG_TOOLS
from app.agents.llms import rag_llm
from app.agents.prompts import RAG_SYSTEM_PROMPT
from app.agents.formatters.rag_formatter import RagOutput


rag_agent = create_agent(
    model=rag_llm(),
    tools=RAG_TOOLS,
    system_prompt=RAG_SYSTEM_PROMPT,
    response_format=RagOutput,
    name='RAG_Agent',
)