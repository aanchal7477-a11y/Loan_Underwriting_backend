
import logging
from google.adk.agents import Agent
from google.adk.agents import SequentialAgent

from google.adk.tools.agent_tool import AgentTool
from sub_agent.doc_parsing_agent.agent import doc_parsing_agent
from sub_agent.rules_agent.agent import rules_agent
from sub_agent.storage_agent.agent import storage_agent


logger = logging.getLogger("orchestrator")

# ---------------------------
# Orchestrator Agent
# ---------------------------
orchestrator_agent = SequentialAgent(
    name="orchestrator_agent",
    description="Main loan underwriting agent",
    sub_agents=[doc_parsing_agent, rules_agent, storage_agent],
)

