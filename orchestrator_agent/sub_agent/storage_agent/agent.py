from google.adk.agents import Agent
from .tools import save_to_bigquery
from .prompt import STORAGE_PROMPT

storage_agent = Agent(
    name="storage_agent",
    model="gemini-2.0-flash",
    description="Saves loan underwriting results to BigQuery",
    instruction=STORAGE_PROMPT,
    tools=[save_to_bigquery],
)
