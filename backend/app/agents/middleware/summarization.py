from langchain.agents.middleware import SummarizationMiddleware

from app.agents.llms import summarization_llm


summarization = SummarizationMiddleware(
    summarization_llm(),
    trigger=[
        ("tokens", 20_000),
    ],
)