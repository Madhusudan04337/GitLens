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

@mcp.tool()
async def generate_card_html(username: str, github_data: dict, analysis: dict) -> str:
    """Generate a premium landscape-oriented HTML dev card."""
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
    
    skills_html = "".join([f'<span class="px-3 py-1.5 rounded-full text-[11px] font-bold uppercase tracking-wider {cfg["accent"]} border {cfg["border"]}">{skill}</span>' for skill in analysis.get("top_skills", [])[:4]])
    
    repos_html = "".join([
        f'''
        <div class="flex-1 min-w-0 p-4 border rounded-2xl {cfg["border"]} {cfg["card"]} hover:translate-y-[-4px] transition-all duration-300">
            <h4 class="font-bold text-[13px] truncate mb-1">{repo["name"]}</h4>
            <p class="text-[11px] {cfg["secondary"]} line-clamp-2 mb-3 h-8 leading-snug">{repo["description"] or "No description provided."}</p>
            <div class="flex justify-between items-center text-[11px] font-bold">
                <span class="flex items-center gap-1.5">
                    <svg class="w-3 h-3 text-yellow-500" fill="currentColor" viewBox="0 0 20 20"><path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z"></path></svg>
                    {repo["stars"]}
                </span>
                <span class="px-2 py-0.5 rounded-md {cfg["accent"]} border {cfg["border"]} text-[9px] uppercase">{repo["language"] or "Code"}</span>
            </div>
        </div>
        ''' for repo in github_data.get("top_repos", [])[:3]
    ])

    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <script src="https://cdn.tailwindcss.com"></script>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');
            body {{ 
                font-family: 'Plus Jakarta Sans', sans-serif; 
                margin: 0; 
                display: flex; 
                align-items: center; 
                justify-content: center; 
                min-height: 100vh;
                background-color: transparent;
            }}
            .card-glass {{ 
                backdrop-filter: blur(20px) saturate(160%);
                -webkit-backdrop-filter: blur(20px) saturate(160%);
            }}
            .text-balance {{ text-wrap: balance; }}
        </style>
    </head>
    <body class="p-0 md:p-10 {cfg["text"]}">
        <div class="w-full max-w-[840px] h-auto min-h-[540px] relative overflow-hidden rounded-none md:rounded-[3rem] border-0 md:border-2 {cfg["border"]} {cfg["glow"]} flex flex-col {cfg["card"]} md:card-glass">
            <!-- Decorative background elements -->
            <div class="absolute -top-24 -right-24 w-80 h-80 rounded-full blur-[100px] opacity-20 {cfg["accent"]}"></div>
            <div class="absolute -bottom-24 -left-24 w-80 h-80 rounded-full blur-[100px] opacity-15 {cfg["accent"]}"></div>
            <!-- ================= MOBILE VIEW ================= -->
            <div class="md:hidden flex flex-col p-6">
                <!-- Mobile Header -->
                <div class="flex items-center gap-5 mb-6">
                    <div class="relative">
                        <div class="absolute -inset-2 rounded-[2rem] blur-md opacity-30 {cfg["accent"]}"></div>
                        <img src="{github_data.get("avatar_url")}" class="relative w-24 h-24 rounded-[1.5rem] border-2 {cfg["border"]} shadow-2xl object-cover ring-2 ring-white/10">
                    </div>
                    <div class="flex flex-col">
                        <h2 class="text-2xl font-extrabold leading-tight tracking-tight">{github_data.get("name")}</h2>
                        <p class="text-sm font-semibold opacity-40 italic">@{username}</p>
                    </div>
                </div>

                <!-- Quote -->
                <div class="relative mb-6 pt-2 pl-4">
                    <span class="absolute left-0 -top-2 text-4xl opacity-10 font-serif">"</span>
                    <p class="text-[15px] font-medium leading-relaxed opacity-90 text-balance">
                        {analysis.get("developer_vibe")}
                    </p>
                </div>

                <!-- Stats -->
                <div class="grid grid-cols-2 gap-4 mb-6">
                    <div class="p-4 rounded-2xl {cfg["stat_bg"]} border {cfg["border"]} flex flex-col items-center shadow-sm text-center">
                        <span class="text-[10px] uppercase font-bold opacity-40 tracking-[0.2em] mb-1">Repositories</span>
                        <span class="text-3xl font-extrabold">{github_data.get("public_repos")}</span>
                    </div>
                    <div class="p-4 rounded-2xl {cfg["stat_bg"]} border {cfg["border"]} flex flex-col items-center shadow-sm text-center">
                        <span class="text-[10px] uppercase font-bold opacity-40 tracking-[0.2em] mb-1">Followers</span>
                        <span id="mobile-followers-count" class="text-3xl font-extrabold transition-all duration-300">{github_data.get("followers")}</span>
                    </div>
                </div>

                <!-- Skills -->
                <div class="flex flex-wrap justify-center gap-2.5 mb-6">
                    {skills_html}
                </div>

                <!-- Profile Actions -->
                <div class="flex gap-3 mb-8 px-4 justify-center w-full">
                    <button onclick="handleFollow()" id="mobile-follow-btn" class="flex-1 py-2.5 px-4 rounded-xl border font-bold text-xs flex items-center justify-center gap-2 transition-all duration-300 hover:scale-[1.02] active:scale-[0.98] cursor-pointer {cfg['accent']} {cfg['border']}">
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z"></path></svg>
                        <span id="mobile-follow-text">Follow</span>
                    </button>
                    <a href="https://github.com/{username}" target="_blank" class="flex-1 py-2.5 px-4 rounded-xl border font-bold text-xs flex items-center justify-center gap-2 transition-all duration-300 hover:scale-[1.02] active:scale-[0.98] {cfg['accent']} {cfg['border']} opacity-80 hover:opacity-100">
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"></path></svg>
                        <span>GitHub</span>
                    </a>
                </div>

                <!-- Repositories -->
                <div class="mb-6">
                    <h3 class="text-[11px] font-black uppercase mb-4 opacity-30 tracking-[0.4em] text-center">{github_data.get("repos_type", "Signature Projects")}</h3>
                    <div class="flex flex-col gap-3">
                        {repos_html}
                    </div>
                </div>

                <!-- Footer -->
                <div class="mt-auto pt-6 border-t {cfg["border"]} flex flex-col items-center text-center gap-4">
                    <div class="flex items-center gap-3">
                        <div class="flex gap-1">
                            <span class="w-1.5 h-1.5 rounded-full bg-blue-500 animate-pulse"></span>
                            <span class="w-1.5 h-1.5 rounded-full bg-purple-500 animate-pulse" style="animation-delay: 0.2s"></span>
                            <span class="w-1.5 h-1.5 rounded-full bg-pink-500 animate-pulse" style="animation-delay: 0.4s"></span>
                        </div>
                        <span class="text-[10px] font-black uppercase tracking-[0.2em] opacity-40">Verification ID:<br/>{username.upper()}</span>
                    </div>
                    <span class="opacity-60 italic normal-case font-medium text-[11px] text-balance leading-relaxed px-4">{analysis.get("fun_fact", "")}</span>
                    <span class="text-[11px] font-bold uppercase tracking-widest opacity-80 mt-2">Dev Card AI 2026</span>
                    <span class="text-[7px] opacity-20 uppercase tracking-tighter">Rendered via GraphQL v4 • Pinned Priority Mode</span>
                </div>
            </div>

            <!-- ================= DESKTOP VIEW ================= -->
            <div class="hidden md:flex flex-col h-full w-full">
                <div class="flex-1 flex p-10 gap-10">
                    <!-- Left: Profile Info -->
                    <div class="w-[30%] flex flex-col items-center text-center">
                        <div class="relative mb-8">
                            <div class="absolute -inset-2 rounded-[2.5rem] blur-md opacity-30 {cfg["accent"]}"></div>
                            <img src="{github_data.get("avatar_url")}" class="relative w-36 h-36 rounded-[2.2rem] border-2 {cfg["border"]} shadow-2xl object-cover ring-4 ring-white/10">
                        </div>
                        <h2 class="text-3xl font-extrabold leading-tight mb-2 tracking-tight">{github_data.get("name")}</h2>
                        <p class="text-base font-semibold opacity-40 mb-6 italic">@{username}</p>
                        <div class="flex flex-wrap justify-center gap-2.5 mb-6">
                            {skills_html}
                        </div>
                        <!-- Profile Actions -->
                        <div class="flex w-full gap-3 px-2">
                            <button onclick="handleFollow()" id="desktop-follow-btn" class="flex-1 py-2.5 px-4 rounded-xl border font-bold text-xs flex items-center justify-center gap-2 transition-all duration-300 hover:scale-[1.02] active:scale-[0.98] cursor-pointer {cfg['accent']} {cfg['border']}">
                                <svg class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z"></path></svg>
                                <span id="desktop-follow-text">Follow</span>
                            </button>
                            <a href="https://github.com/{username}" target="_blank" class="flex-1 py-2.5 px-4 rounded-xl border font-bold text-xs flex items-center justify-center gap-2 transition-all duration-300 hover:scale-[1.02] active:scale-[0.98] {cfg['accent']} {cfg['border']} opacity-80 hover:opacity-100">
                                <svg class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"></path></svg>
                                <span>GitHub</span>
                            </a>
                        </div>
                    </div>
                    
                    <!-- Right: Stats and Content -->
                    <div class="w-[70%] flex flex-col">
                        <div class="flex-1">
                            <div class="relative mb-8 pt-2">
                                <span class="absolute -left-6 -top-2 text-5xl opacity-10 font-serif">"</span>
                                <p class="text-[17px] font-medium leading-relaxed opacity-90 pr-6 text-balance">
                                    {analysis.get("developer_vibe")}
                                </p>
                            </div>
                            
                            <div class="grid grid-cols-2 gap-5 mb-10">
                                <div class="p-5 rounded-3xl {cfg["stat_bg"]} border {cfg["border"]} flex flex-col items-start shadow-sm">
                                    <span class="text-[12px] uppercase font-bold opacity-40 tracking-[0.2em] mb-1">Repositories</span>
                                    <span class="text-4xl font-extrabold">{github_data.get("public_repos")}</span>
                                </div>
                                <div class="p-5 rounded-3xl {cfg["stat_bg"]} border {cfg["border"]} flex flex-col items-start shadow-sm">
                                    <span class="text-[12px] uppercase font-bold opacity-40 tracking-[0.2em] mb-1">Followers</span>
                                    <span id="desktop-followers-count" class="text-4xl font-extrabold transition-all duration-300">{github_data.get("followers")}</span>
                                </div>
                            </div>
                        </div>
                        
                        <div class="mt-auto">
                            <h3 class="text-[11px] font-black uppercase mb-4 opacity-30 tracking-[0.4em]">{github_data.get("repos_type", "Signature Projects")}</h3>
                            <div class="flex gap-4">
                                {repos_html}
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Footer -->
                <div class="px-10 py-6 border-t {cfg["border"]} flex justify-between items-center bg-white/5">
                    <div class="flex items-center gap-4">
                        <div class="flex gap-1">
                            <span class="w-1.5 h-1.5 rounded-full bg-blue-500 animate-pulse"></span>
                            <span class="w-1.5 h-1.5 rounded-full bg-purple-500 animate-pulse" style="animation-delay: 0.2s"></span>
                            <span class="w-1.5 h-1.5 rounded-full bg-pink-500 animate-pulse" style="animation-delay: 0.4s"></span>
                        </div>
                        <span class="text-[11px] font-black uppercase tracking-[0.2em] opacity-40">Verification ID: {username.upper()}</span>
                    </div>
                    <div class="flex items-center gap-6 text-[11px] font-bold uppercase tracking-widest">
                        <span class="opacity-60 italic normal-case font-medium">{analysis.get("fun_fact", "")}</span>
                        <div class="h-4 w-px {cfg["border"]}"></div>
                        <span class="opacity-80">Dev Card AI 2026</span>
                    </div>
                    <span class="text-[8px] opacity-20 uppercase tracking-tighter">Rendered via GraphQL v4 • Pinned Priority Mode</span>
                </div>
            </div>
        </div>
        <script>
            let followed = false;
            const originalCount = {github_data.get("followers")};
            
            function handleFollow() {{
                if (followed) return;
                followed = true;
                
                // Update Follower Counts
                const mobileCountEl = document.getElementById("mobile-followers-count");
                const desktopCountEl = document.getElementById("desktop-followers-count");
                if (mobileCountEl) {{
                    mobileCountEl.textContent = originalCount + 1;
                    mobileCountEl.classList.add("scale-125", "text-green-500");
                    setTimeout(() => mobileCountEl.classList.remove("scale-125"), 300);
                }}
                if (desktopCountEl) {{
                    desktopCountEl.textContent = originalCount + 1;
                    desktopCountEl.classList.add("scale-125", "text-green-500");
                    setTimeout(() => desktopCountEl.classList.remove("scale-125"), 300);
                }}
                
                // Update buttons to show Following state
                const mobileText = document.getElementById("mobile-follow-text");
                const desktopText = document.getElementById("desktop-follow-text");
                if (mobileText) mobileText.textContent = "Following";
                if (desktopText) desktopText.textContent = "Following";
                
                const mobileBtn = document.getElementById("mobile-follow-btn");
                const desktopBtn = document.getElementById("desktop-follow-btn");
                
                const disabledClasses = ["opacity-60", "cursor-not-allowed"];
                if (mobileBtn) {{
                    mobileBtn.classList.add(...disabledClasses);
                    mobileBtn.removeAttribute("onclick");
                }}
                if (desktopBtn) {{
                    desktopBtn.classList.add(...disabledClasses);
                    desktopBtn.removeAttribute("onclick");
                }}
                
                // Open user's GitHub profile in a new tab to complete follow on GitHub
                window.open("https://github.com/{username}", "_blank");
            }}
        </script>
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
