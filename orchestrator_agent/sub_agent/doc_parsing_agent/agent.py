from google.adk.agents import Agent
from .tools import process_and_parse_docs
from .prompt import DOC_PARSING_PROMPT

doc_parsing_agent = Agent(
    name="doc_parsing_agent",
    model="gemini-2.0-flash",
    description="Agent to process documents with DocAI and parse fields",
    instruction=DOC_PARSING_PROMPT,
    tools=[process_and_parse_docs],
)
