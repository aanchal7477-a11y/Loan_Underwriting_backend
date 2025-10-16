from google.adk.agents import Agent
from .tools import loan_approval
from .prompt import RULES_PROMPT

rules_agent = Agent(
    name="rules_agent",
    model="gemini-2.0-flash",
    description="Applies underwriting rules for loan approval",
    instruction=RULES_PROMPT,
    tools=[loan_approval],
)
