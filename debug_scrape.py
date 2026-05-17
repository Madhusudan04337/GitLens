import os
import asyncio
from backend.mcp_server import scrape_github
from pathlib import Path
from dotenv import load_dotenv

async def main():
    # Force load env from root
    root_env = Path(__file__).parent.absolute() / ".env"
    print(f"Loading env from: {root_env}")
    load_dotenv(root_env)
    
    token = os.getenv("GITHUB_TOKEN")
    print(f"Token found: {token[:10]}..." if token else "Token NOT found")
    
    username = "Madhusudan04337"
    print(f"Scraping {username}...")
    result = await scrape_github(username)
    
    if "error" in result:
        print(f"Error: {result['error']}")
    else:
        print(f"Repos type: {result.get('repos_type')}")
        print(f"Top repos: {[r['name'] for r in result.get('top_repos', [])]}")

if __name__ == "__main__":
    asyncio.run(main())
