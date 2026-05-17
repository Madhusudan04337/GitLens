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
    """Generate a premium landscape-oriented HTML dev card."""
    theme = analysis.get("card_theme", "builder")
    
    theme_configs = {
        "hacker": {"bg": "bg-[#0a0a0a]", "text": "text-green-400", "border": "border-green-900", "accent": "bg-green-900/30", "card": "bg-black/80"},
        "builder": {"bg": "bg-[#f8fafc]", "text": "text-slate-900", "border": "border-blue-200", "accent": "bg-blue-500/10", "card": "bg-white/80"},
        "researcher": {"bg": "bg-[#ffffff]", "text": "text-gray-900", "border": "border-gray-200", "accent": "bg-gray-100", "card": "bg-white/90"},
        "designer": {"bg": "bg-[#faf5ff]", "text": "text-purple-900", "border": "border-purple-200", "accent": "bg-purple-500/10", "card": "bg-white/80"},
        "open-source-hero": {"bg": "bg-[#fffbeb]", "text": "text-yellow-900", "border": "border-yellow-200", "accent": "bg-yellow-500/10", "card": "bg-white/80"}
    }
    
    cfg = theme_configs.get(theme, theme_configs["builder"])
    
    skills_html = "".join([f'<span class="px-2 py-0.5 rounded-md text-[10px] font-bold uppercase tracking-wider {cfg["accent"]}">{skill}</span>' for skill in analysis.get("top_skills", [])])
    
    repos_html = "".join([
        f'''
        <div class="flex-1 p-2 border rounded-lg {cfg["border"]} {cfg["card"]} shadow-sm">
            <h4 class="font-bold text-[11px] truncate">{repo["name"]}</h4>
            <p class="text-[9px] opacity-70 line-clamp-1 mb-1">{repo["description"] or "No description"}</p>
            <div class="flex justify-between items-center text-[8px] font-bold">
                <span class="flex items-center gap-1">⭐ {repo["stars"]}</span>
                <span class="opacity-60">{repo["language"] or ""}</span>
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
            @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;800&display=swap');
            body {{ font-family: 'Plus Jakarta Sans', sans-serif; height: 100vh; margin: 0; display: flex; align-items: center; justify-content: center; }}
            .card-glass {{ backdrop-filter: blur(10px); }}
        </style>
    </head>
    <body class="p-2 {cfg["bg"]} {cfg["text"]}">
        <div class="w-[600px] h-[320px] relative overflow-hidden rounded-2xl border-2 {cfg["border"]} shadow-2xl flex flex-col {cfg["card"]} card-glass">
            <!-- Decorative background blob -->
            <div class="absolute -top-10 -right-10 w-40 h-40 rounded-full blur-3xl opacity-20 {cfg["accent"]}"></div>
            
            <div class="flex-1 flex p-6 gap-6">
                <!-- Left: Profile Info -->
                <div class="w-1/3 flex flex-col items-center text-center justify-center border-r {cfg["border"]} pr-6">
                    <img src="{github_data.get("avatar_url")}" class="w-24 h-24 rounded-2xl border-2 {cfg["border"]} shadow-lg mb-4 object-cover transform rotate-1">
                    <h2 class="text-xl font-extrabold leading-tight mb-1">{github_data.get("name")}</h2>
                    <p class="text-xs font-bold opacity-50 mb-3">@{username}</p>
                    <div class="flex flex-wrap justify-center gap-1.5">
                        {skills_html}
                    </div>
                </div>
                
                <!-- Right: Stats and Content -->
                <div class="w-2/3 flex flex-col justify-between py-2">
                    <div>
                        <p class="text-sm italic leading-relaxed mb-4 opacity-90">"{analysis.get("developer_vibe")}"</p>
                        
                        <div class="grid grid-cols-2 gap-3 mb-4">
                            <div class="p-2.5 rounded-xl {cfg["accent"]} border {cfg["border"]}">
                                <div class="text-[10px] uppercase font-bold opacity-50 mb-0.5">Repositories</div>
                                <div class="text-xl font-extrabold">{github_data.get("public_repos")}</div>
                            </div>
                            <div class="p-2.5 rounded-xl {cfg["accent"]} border {cfg["border"]}">
                                <div class="text-[10px] uppercase font-bold opacity-50 mb-0.5">Followers</div>
                                <div class="text-xl font-extrabold">{github_data.get("followers")}</div>
                            </div>
                        </div>
                    </div>
                    
                    <div>
                        <h3 class="text-[10px] font-extrabold uppercase mb-2 opacity-40 tracking-[0.2em]">Signature Repositories</h3>
                        <div class="flex gap-2">
                            {repos_html}
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Footer -->
            <div class="px-6 py-2.5 border-t {cfg["border"]} flex justify-between items-center text-[9px] font-bold uppercase tracking-wider opacity-60 bg-white/5">
                <span>Verification ID: {username.upper()}-GEN-2026</span>
                <span class="flex items-center gap-2">
                    {analysis.get("fun_fact", "")}
                    <span class="h-1 w-1 rounded-full bg-current"></span>
                    Dev Card AI
                </span>
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
