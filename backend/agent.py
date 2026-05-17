from google import adk
from .mcp_server import mcp

# Define the ADK Agent
agent = adk.Agent(
    name="GitHubDevCardAgent",
    instructions="You are a creative developer assistant that generates personalized GitHub developer cards.",
    tools=mcp.tools
)

async def run_agent(prompt: str):
    """Run the agent with a given prompt."""
    response = await agent.run(prompt)
    return response
