from langchain.agents import create_agent
from langchain.agents.middleware import dynamic_prompt, ModelRequest

from app.agents.llms import orchestrator_llm
from app.agents.persistence.checkpointer import get_checkpointer
from app.agents.tools.orchestrator_tools import ORCHESTRATOR_TOOLS
from app.agents.runtime_context import AgentContext
from app.agents.prompts import orchestrator_base
from app.agents.middleware.pii import pii_middleware
from app.agents.middleware.summarization import summarization



@dynamic_prompt
async def context_aware_prompt(request: ModelRequest):
    base = orchestrator_base
    context = request.runtime.context
    prompt_context = f"\n\nThe context of the current conversation:\nUser id: {context.user_id}\nuser name: {context.user_name}\nuser files: {context.files}"
    return base + prompt_context

async def get_orchestrator():
    orchestrator = create_agent(
        model=orchestrator_llm(),
        tools=ORCHESTRATOR_TOOLS,
        middleware=[
            context_aware_prompt,
            *pii_middleware,
            summarization,
        ],
        checkpointer=get_checkpointer(),
        context_schema=AgentContext,
        name='Inkris_Orchestrator'
    )
    return orchestrator