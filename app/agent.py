import sys
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator

from langchain_anthropic import ChatAnthropic
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.tools import load_mcp_tools
from langgraph.prebuilt import create_react_agent

MCP_SERVER = Path(__file__).parent.parent / "mcp_server" / "server.py"

SYSTEM_PROMPT = """\
You are an AI clinical decision support assistant for Mercy Regional Medical Center Emergency Department.

You have direct access to the hospital's patient database via database tools. You can:
- Look up patients by MRN or name
- Retrieve triage records, vital signs, allergies, and medications
- Pull today's census and ESI statistics
- Identify critical/high-acuity patients
- Insert new patient intake records

Guidelines:
- Always flag known allergies when discussing medications
- Highlight ESI 1-2 patients as critical
- Abnormal vitals: HR >100 or <60, SBP <90 or >180, SpO2 <95%, Temp >38.3°C or <36°C
- Be concise and clinically precise — format tables/lists when it helps readability
- Remind staff to follow institutional protocols for clinical decisions
- The sample census date is 2025-04-28
"""

_MCP_CONFIG = {
    "ed_database": {
        "command": sys.executable,
        "args": [str(MCP_SERVER)],
        "transport": "stdio",
    }
}


@asynccontextmanager
async def agent_session() -> AsyncIterator:
    """Context manager that yields a ready-to-use agent for one request."""
    client = MultiServerMCPClient(_MCP_CONFIG)
    async with client.session("ed_database") as session:
        tools = await load_mcp_tools(session)
        llm = ChatAnthropic(model="claude-sonnet-4-6", temperature=0, max_tokens=2048)
        agent = create_react_agent(llm, tools, prompt=SYSTEM_PROMPT)
        yield agent
