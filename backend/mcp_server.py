import os
import json
import httpx
from mcp.server.fastmcp import FastMCP
import google.generativeai as genai
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

# Initialize FastMCP server
mcp = FastMCP("GitHub-Dev-Card-Server")

# Configure Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-1.5-flash-latest") # Stable free tier model

@mcp.tool()
async def scrape_github(username: str) -> dict:
    """Fetch GitHub profile data and top repositories."""
    headers = {}
    github_token = os.getenv("GITHUB_TOKEN")
    if github_token:
        headers["Authorization"] = f"token {github_token}"

    async with httpx.AsyncClient(headers=headers) as client:
        # Fetch user profile
        user_resp = await client.get(f"https://api.github.com/users/{username}")
        if user_resp.status_code != 200:
            return {"error": f"Failed to fetch user {username}: {user_resp.status_code}"}
        user_data = user_resp.json()

        # Fetch top repositories
        repos_resp = await client.get(f"https://api.github.com/users/{username}/repos?sort=updated&per_page=10")
        repos_data = repos_resp.json()

    # Process repos
    top_repos = []
    languages = {}
    for repo in repos_data:
        if not repo.get("fork") and len(top_repos) < 6:
            top_repos.append({
                "name": repo["name"],
                "stars": repo["stargazers_count"],
                "language": repo["language"],
                "description": repo["description"]
            })
        if repo.get("language"):
            lang = repo["language"]
            languages[lang] = languages.get(lang, 0) + 1

    # Sort languages by usage
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
        "top_languages": top_languages
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

@mcp.tool()
async def generate_card_html(username: str, github_data: dict, analysis: dict) -> str:
    """Generate a self-contained HTML dev card."""
    theme = analysis.get("card_theme", "builder")
    
    theme_configs = {
        "hacker": {"bg": "bg-gray-900", "text": "text-green-400", "border": "border-green-500", "accent": "bg-green-900/50"},
        "builder": {"bg": "bg-blue-50", "text": "text-blue-900", "border": "border-blue-300", "accent": "bg-blue-100"},
        "researcher": {"bg": "bg-white", "text": "text-gray-800", "border": "border-gray-200", "accent": "bg-gray-50"},
        "designer": {"bg": "bg-purple-50", "text": "text-purple-900", "border": "border-purple-300", "accent": "bg-purple-100"},
        "open-source-hero": {"bg": "bg-yellow-50", "text": "text-yellow-900", "border": "border-yellow-300", "accent": "bg-yellow-100"}
    }
    
    cfg = theme_configs.get(theme, theme_configs["builder"])
    
    skills_html = "".join([f'<span class="px-2 py-1 rounded-full text-xs font-semibold {cfg["accent"]}">{skill}</span>' for skill in analysis.get("top_skills", [])])
    
    repos_html = "".join([
        f'''
        <div class="p-3 border rounded {cfg["border"]} {cfg["accent"]}">
            <h4 class="font-bold text-sm">{repo["name"]}</h4>
            <p class="text-xs opacity-80 mb-1">{repo["description"] or "No description"}</p>
            <div class="flex justify-between text-[10px]">
                <span>⭐ {repo["stars"]}</span>
                <span>{repo["language"] or ""}</span>
            </div>
        </div>
        ''' for repo in github_data.get("top_repos", [])[:3]
    ])

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <script src="https://cdn.tailwindcss.com"></script>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700&display=swap');
            body {{ font-family: 'Inter', sans-serif; }}
        </style>
    </head>
    <body class="p-4 {cfg["bg"]} {cfg["text"]}">
        <div class="max-w-sm mx-auto border-2 rounded-xl overflow-hidden {cfg["border"]} shadow-2xl">
            <div class="p-6">
                <div class="flex items-center gap-4 mb-4">
                    <img src="{github_data.get("avatar_url")}" class="w-20 h-20 rounded-full border-2 {cfg["border"]}">
                    <div>
                        <h2 class="text-xl font-bold">{github_data.get("name")}</h2>
                        <p class="text-sm opacity-70">@{username}</p>
                    </div>
                </div>
                
                <p class="text-sm italic mb-4">"{analysis.get("developer_vibe")}"</p>
                
                <div class="flex flex-wrap gap-2 mb-6">
                    {skills_html}
                </div>
                
                <div class="grid grid-cols-2 gap-4 mb-6 text-center">
                    <div class="p-2 rounded {cfg["accent"]}">
                        <div class="text-xl font-bold">{github_data.get("public_repos")}</div>
                        <div class="text-[10px] uppercase">Repos</div>
                    </div>
                    <div class="p-2 rounded {cfg["accent"]}">
                        <div class="text-xl font-bold">{github_data.get("followers")}</div>
                        <div class="text-[10px] uppercase">Followers</div>
                    </div>
                </div>
                
                <h3 class="text-xs font-bold uppercase mb-3 opacity-60 tracking-widest">Top Repositories</h3>
                <div class="space-y-3">
                    {repos_html}
                </div>
                
                <div class="mt-6 pt-4 border-t {cfg["border"]} text-[10px] opacity-50 flex justify-between">
                    <span>Generated by GitHub Dev Card</span>
                    <span>{analysis.get("fun_fact", "")}</span>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    return html

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
