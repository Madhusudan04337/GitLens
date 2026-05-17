import os
from google import adk
from google.adk.toolsets import McpToolset
from google.adk.toolsets.mcp import LocalServerConfig

# Configure the local MCP server path
mcp_server_path = os.path.join(os.path.dirname(__file__), "mcp_server.py")

# Define the ADK Agent
github_card_agent = adk.Agent(
    name="github_card_agent",
    model="gemini-2.0-flash", # Using 2.0-flash for agent reasoning
    instructions="""You are a GitHub profile analyst and dev card generator. 
    When a user gives you a GitHub username, you ALWAYS follow this exact sequence: 
    1. Call scrape_github to fetch profile data.
    2. Call analyze_profile with the scraping result to determine vibe and theme.
    3. Call generate_card_html with the username, scraping result, and analysis.
    4. Call save_card with the final HTML.
    
    Never skip steps. Be enthusiastic about developers' work. 
    If the profile is private or doesn't exist, say so clearly.""",
    toolsets=[
        McpToolset(
            servers=[
                LocalServerConfig(
                    command="python",
                    args=[mcp_server_path]
                )
            ]
        )
    ]
)

# Keep for backward compatibility or simple testing
async def run_agent(prompt: str):
    """Run the agent with a given prompt."""
    response = await github_card_agent.run(prompt)
    return response
