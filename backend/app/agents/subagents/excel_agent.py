from langchain.agents import create_agent

from app.agents.tools.excel_tools import EXCEL_TOOLS
from app.agents.llms import orchestrator_llm
from app.agents.prompts import EXCEL_AGENT_PROMPT


excel_agent = create_agent(
    model=orchestrator_llm(), # Use the stronger models as the tools are highly complex
    tools=EXCEL_TOOLS,
    system_prompt=EXCEL_AGENT_PROMPT,
    name='Excel_Agent',
)