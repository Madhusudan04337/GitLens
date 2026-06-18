import os
import json
import httpx
from mcp.server.fastmcp import FastMCP
import google.generativeai as genai
from dotenv import load_dotenv
from pathlib import Path

# Find .env in project root
project_root = Path(__file__).parent.parent.absolute()
load_dotenv(project_root / ".env")

# Initialize FastMCP server
mcp = FastMCP("GitHub-Dev-Card-Server")

# Configure Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-1.5-flash-latest") # Stable free tier model

@mcp.tool()
async def scrape_github(username: str) -> dict:
    """Fetch GitHub profile data and prioritize pinned repositories."""
    github_token = os.getenv("GITHUB_TOKEN")
    
    headers = {"Accept": "application/vnd.github.v3+json"}
    if github_token:
        headers["Authorization"] = f"token {github_token}"

    async with httpx.AsyncClient(headers=headers, timeout=10.0) as client:
        # Fetch user profile
        user_resp = await client.get(f"https://api.github.com/users/{username}")
        if user_resp.status_code in (401, 403) and github_token:
            print(f"Warning: GitHub API returned status {user_resp.status_code} with token. Retrying without token...")
            github_token = None
            if "Authorization" in client.headers:
                del client.headers["Authorization"]
            user_resp = await client.get(f"https://api.github.com/users/{username}")

        if user_resp.status_code != 200:
            return {"error": f"Failed to fetch user {username}: {user_resp.status_code}"}
        user_data = user_resp.json()

        top_repos = []
        repos_type = "Recent Repositories"

        # Try to fetch Pinned Repositories via GraphQL if token is available
        if github_token:
            print(f"Attempting GraphQL for {username}...")
            gql_query = {
                "query": """
                query($username: String!) {
                  user(login: $username) {
                    pinnedItems(first: 6, types: REPOSITORY) {
                      nodes {
                        ... on Repository {
                          name
                          description
                          stargazerCount
                          primaryLanguage {
                            name
                          }
                        }
                      }
                    }
                  }
                }
                """,
                "variables": {"username": username}
            }
            try:
                gql_resp = await client.post(
                    "https://api.github.com/graphql",
                    json=gql_query,
                    headers={"Authorization": f"Bearer {github_token}"}
                )
                if gql_resp.status_code == 200:
                    gql_data = gql_resp.json()
                    if "errors" in gql_data:
                        print(f"GraphQL Errors: {gql_data['errors']}")
                    else:
                        nodes = gql_data.get("data", {}).get("user", {}).get("pinnedItems", {}).get("nodes", [])
                        if nodes:
                            print(f"Found {len(nodes)} pinned repos.")
                            for node in nodes:
                                top_repos.append({
                                    "name": node["name"],
                                    "stars": node["stargazerCount"],
                                    "language": node.get("primaryLanguage", {}).get("name") if node.get("primaryLanguage") else "Code",
                                    "description": node["description"]
                                })
                            repos_type = "Signature Projects"
                else:
                    print(f"GraphQL Failed with status {gql_resp.status_code}: {gql_resp.text}")
                    if gql_resp.status_code in (401, 403):
                        print("Clearing token due to GraphQL authentication failure.")
                        github_token = None
                        if "Authorization" in client.headers:
                            del client.headers["Authorization"]
            except Exception as e:
                print(f"GraphQL Exception: {e}")
        else:
            print("No GITHUB_TOKEN found, skipping GraphQL.")

        # Fallback to Recent Repositories if no pinned repos found
        if not top_repos:
            print(f"Falling back to REST for {username}...")
            repos_resp = await client.get(f"https://api.github.com/users/{username}/repos?sort=updated&per_page=10")
            if repos_resp.status_code == 200:
                repos_data = repos_resp.json()
                for repo in repos_data:
                    if not repo.get("fork") and len(top_repos) < 6:
                        top_repos.append({
                            "name": repo["name"],
                            "stars": repo["stargazers_count"],
                            "language": repo["language"],
                            "description": repo["description"]
                        })
                repos_type = "Recent Repositories"

    # Calculate top languages from recent repos (for analysis)
    languages = {}
    # We might need a separate call for full language stats if we want to be thorough, 
    # but for vibe analysis, the language of the fetched repos is usually enough.
    for repo in top_repos:
        if repo.get("language"):
            lang = repo["language"]
            languages[lang] = languages.get(lang, 0) + 1

    sorted_langs = sorted(languages.items(), key=lambda x: x[1], reverse=True)
    top_languages = [lang for lang, count in sorted_langs[:5]]

    return {
        "name": user_data.get("name") or username,
        "avatar_url": user_data.get("avatar_url"),
        "bio": user_data.get("bio", ""),
        "location": user_data.get("location", "Unknown"),
        "public_repos": user_data.get("public_repos", 0),
        "followers": user_data.get("followers", 0),
        "top_repos": top_repos,
        "top_languages": top_languages,
        "repos_type": repos_type
    }

@mcp.tool()
async def analyze_profile(github_data: dict) -> dict:
    """Analyze GitHub data using Gemini to determine vibe and theme."""
    prompt = f"""
    Analyze this GitHub profile data and return a JSON object.
    
    Data: {json.dumps(github_data)}
    
    Expected JSON format:
    {{
        "developer_vibe": "A one sentence creative personality description.",
        "top_skills": ["Skill1", "Skill2", "Skill3"],
        "fun_fact": "A clever observation based on their repos or bio.",
        "card_theme": "hacker" | "builder" | "researcher" | "designer" | "open-source-hero"
    }}
    """
    
    try:
        response = model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
        return json.loads(response.text)
    except Exception as e:
        print(f"Gemini API Error: {e}. Falling back to mock analysis.")
        # Mock fallback analysis
        return {
            "developer_vibe": f"A dedicated developer with {github_data.get('public_repos')} repos and a passion for {github_data.get('top_languages', ['coding'])[0]}.",
            "top_skills": github_data.get("top_languages", ["Python", "JavaScript", "Cloud"])[:3],
            "fun_fact": "This developer's code is so clean, it cleans the screen.",
            "card_theme": "builder"
        }

from jinja2 import Environment, FileSystemLoader

@mcp.tool()
async def generate_card_html(username: str, github_data: dict, analysis: dict) -> str:
    """Generate a premium landscape-oriented HTML dev card using Jinja2."""
    theme = analysis.get("card_theme", "builder")
    
    theme_configs = {
        "hacker": {
            "bg": "bg-[#020617]", 
            "text": "text-[#22c55e]", 
            "border": "border-[#22c55e]/30", 
            "accent": "bg-[#22c55e]/10", 
            "card": "bg-[#020617]/80",
            "glow": "shadow-[0_0_50px_rgba(34,197,94,0.15)]",
            "stat_bg": "bg-[#22c55e]/5",
            "secondary": "text-[#4ade80]"
        },
        "builder": {
            "bg": "bg-[#f8fafc]", 
            "text": "text-[#0f172a]", 
            "border": "border-[#e2e8f0]", 
            "accent": "bg-[#3b82f6]/10", 
            "card": "bg-white/90",
            "glow": "shadow-[0_20px_50px_rgba(0,0,0,0.05)]",
            "stat_bg": "bg-slate-50",
            "secondary": "text-slate-500"
        },
        "researcher": {
            "bg": "bg-[#fdfdfd]", 
            "text": "text-[#1e293b]", 
            "border": "border-[#cbd5e1]", 
            "accent": "bg-[#64748b]/10", 
            "card": "bg-white/95",
            "glow": "shadow-xl",
            "stat_bg": "bg-slate-50",
            "secondary": "text-slate-500"
        },
        "designer": {
            "bg": "bg-[#faf5ff]", 
            "text": "text-[#4c1d95]", 
            "border": "border-[#ddd6fe]", 
            "accent": "bg-[#8b5cf6]/10", 
            "card": "bg-white/90",
            "glow": "shadow-[0_20px_50px_rgba(139,92,246,0.08)]",
            "stat_bg": "bg-purple-50",
            "secondary": "text-purple-600/70"
        },
        "open-source-hero": {
            "bg": "bg-[#fffbeb]", 
            "text": "text-[#78350f]", 
            "border": "border-[#fde68a]", 
            "accent": "bg-[#f59e0b]/10", 
            "card": "bg-white/90",
            "glow": "shadow-[0_20px_50px_rgba(245,158,11,0.08)]",
            "stat_bg": "bg-amber-50",
            "secondary": "text-amber-700/70"
        }
    }
    
    cfg = theme_configs.get(theme, theme_configs["builder"])
    
    # Setup Jinja2 environment
    template_dir = os.path.join(os.path.dirname(__file__), "templates")
    env = Environment(loader=FileSystemLoader(template_dir))
    template = env.get_template("card_template.html")
    
    return template.render(
        username=username,
        github_data=github_data,
        analysis=analysis,
        cfg=cfg
    )

@mcp.tool()
async def save_card(username: str, html: str) -> str:
    """Save the HTML to static/cards/{username}.html and return the path."""
    try:
        # Use absolute path based on this file's location
        backend_dir = Path(__file__).parent.absolute()
        output_dir = backend_dir / "static" / "cards"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = output_dir / f"{username}.html"
        file_path.write_text(html, encoding="utf-8")
        
        print(f"Tool: Saved card for {username} at {file_path}")
        return f"/static/cards/{username}.html"
    except Exception as e:
        print(f"Tool Error in save_card: {e}")
        return f"Error saving card: {e}"

if __name__ == "__main__":
    mcp.run()
