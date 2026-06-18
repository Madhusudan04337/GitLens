import os
import sys

# Ensure backend directory is in path for absolute imports
sys.path.append(os.path.dirname(__file__))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel
from google.adk import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.memory import InMemoryMemoryService
from google.genai.types import Content, Part
from agent import github_card_agent
from mcp_server import scrape_github, analyze_profile, generate_card_html, save_card

app = FastAPI(title="GitHub Dev Card Generator API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Try sibling directory (local dev)
FRONTEND_DIR = os.path.join(os.path.dirname(BASE_DIR), "frontend")

# Fallback to sub-directory (if copied inside backend dir or app root)
if not os.path.exists(os.path.join(FRONTEND_DIR, "index.html")):
    FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")
STATIC_DIR = os.path.join(BASE_DIR, "static")
CARDS_DIR = os.path.join(STATIC_DIR, "cards")

os.makedirs(CARDS_DIR, exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    """Serve the React frontend from the backend if available, otherwise show a default message."""
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            content = f.read()
            # Replace placeholder if BACKEND_URL is set in environment
            backend_url = os.environ.get("BACKEND_URL", "")
            return content.replace("__BACKEND_URL__", backend_url)
    return "<h1>GitLens Backend API is running!</h1><p>Please use the separate Frontend service URL to view the application.</p>"

# Initialize ADK Services and Runner
session_service = InMemorySessionService()
memory_service = InMemoryMemoryService()
runner = Runner(
    agent=github_card_agent,
    app_name="GitHubCardGenerator",
    session_service=session_service,
    memory_service=memory_service,
    auto_create_session=True
)

class GenerateRequest(BaseModel):
    username: str

@app.post("/generate")
async def generate_card(request: GenerateRequest):
    """
    Tries to run the agent, but falls back to manual tool orchestration 
    if the LLM is unavailable (quota/404) or if the runner fails.
    """
    import time
    timestamp = int(time.time())
    session_id = f"session_{request.username}_{timestamp}"
    message = Content(
        parts=[Part(text=f"Generate a dev card for {request.username}")],
        role="user"
    )
    
    try:
        print(f"[{timestamp}] Attempting Agent orchestration for {request.username}...")
        events = runner.run(
            new_message=message,
            session_id=session_id,
            user_id=request.username
        )
        
        # Consuming events to ensure completion
        for event in events:
            print(f"[{timestamp}] Event: {event}")
            pass
        
        # Check if the card was actually saved
        card_path = os.path.join(CARDS_DIR, f"{request.username}.html")
        if os.path.exists(card_path):
            print(f"[{timestamp}] Agent successfully generated card for {request.username}")
            return {
                "status": "success",
                "username": request.username,
                "card_url": f"/static/cards/{request.username}.html"
            }
        
        print(f"[{timestamp}] Agent finished but card not found. Falling back to Manual Orchestration...")

    except Exception as e:
        print(f"[{timestamp}] Agent failed: {e}. Running Manual Orchestration...")
        
    # Manual Fallback Logic
    try:
        print(f"[{timestamp}] Starting Manual Orchestration for {request.username}...")
        # 1. Scrape
        github_data = await scrape_github(request.username)
        if "error" in github_data:
            print(f"[{timestamp}] Scrape Failed: {github_data['error']}")
            raise HTTPException(status_code=404, detail=github_data["error"])
        
        # 2. Analyze
        print(f"[{timestamp}] Analyzing profile...")
        analysis = await analyze_profile(github_data)
        
        # 3. Generate HTML
        print(f"[{timestamp}] Generating HTML...")
        html = await generate_card_html(request.username, github_data, analysis)
        
        # 4. Save
        print(f"[{timestamp}] Saving card...")
        card_url = await save_card(request.username, html)
        
        if "Error" in card_url:
            raise Exception(card_url)

        print(f"[{timestamp}] Manual orchestration successful for {request.username}")
        return {
            "status": "success",
            "username": request.username,
            "card_url": card_url
        }
    except Exception as manual_e:
        import traceback
        print(f"[{timestamp}] Manual Orchestration Failed:\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(manual_e))

@app.get("/card/{username}")
async def get_card(username: str):
    """Serve the saved HTML card for a specific user."""
    card_path = os.path.join(CARDS_DIR, f"{username}.html")
    if os.path.exists(card_path):
        return FileResponse(card_path)
    else:
        raise HTTPException(status_code=404, detail="Card not found")

@app.get("/health")
def health_check():
    """Health check endpoint for Cloud Run."""
    return {"status": "ok", "service": "github-dev-card-api"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
