from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("GitHub-Dev-Card-Server")

@mcp.tool()
async def fetch_github_profile(username: str) -> str:
    """Fetch GitHub profile data for a given username."""
    # TODO: Implement GitHub API call
    return f"Profile data for {username}"

if __name__ == "__main__":
    mcp.run()
