import os
from dotenv import load_dotenv
from google import adk
from google.adk.tools.mcp_tool import McpToolset, StdioConnectionParams
from mcp.client.stdio import StdioServerParameters

# Load environment variables from .env file
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))

# Ensure GOOGLE_API_KEY is set (ADK and genai libraries use this)
if "GEMINI_API_KEY" in os.environ and "GOOGLE_API_KEY" not in os.environ:
    os.environ["GOOGLE_API_KEY"] = os.environ["GEMINI_API_KEY"]

# Configure the local MCP server path
mcp_server_path = os.path.join(os.path.dirname(__file__), "mcp_server.py")

# Define the ADK Agent
github_card_agent = adk.Agent(
    name="github_card_agent",
    model="gemini-1.5-flash", # Switched to 1.5-flash for quota stability
    instruction="""You are a GitHub profile analyst and dev card generator. 
    When a user gives you a GitHub username, you ALWAYS follow this exact sequence: 
    1. Call scrape_github to fetch profile data.
    2. Call analyze_profile with the scraping result to determine vibe and theme.
    3. Call generate_card_html with the username, scraping result, and analysis.
    4. Call save_card with the final HTML.
    
    Never skip steps. Be enthusiastic about developers' work. 
    If the profile is private or doesn't exist, say so clearly.""",
    tools=[
        McpToolset(
            connection_params=StdioConnectionParams(
                server_params=StdioServerParameters(
                    command="python",
                    args=[mcp_server_path]
                )
            )
        )
    ]
)
