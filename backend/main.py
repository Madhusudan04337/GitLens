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
BASE_DIR = os.path.dirname(__file__)
FRONTEND_DIR = os.path.join(os.path.dirname(BASE_DIR), "frontend")
STATIC_DIR = os.path.join(BASE_DIR, "static")
CARDS_DIR = os.path.join(STATIC_DIR, "cards")

os.makedirs(CARDS_DIR, exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    """Serve the React frontend from the backend."""
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>Frontend index.html not found</h1>"

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
    Creates or reuses a session for the username and runs the agent 
    to orchestrate the card generation sequence.
    """
    session_id = f"session_{request.username}"
    # Construct Content object for new_message
    message = Content(
        parts=[Part(text=f"Generate a dev card for {request.username}")],
        role="user"
    )
    
    try:
        print(f"Generating card for {request.username}...")
        # Run the agent via the ADK Runner
        events = runner.run(
            new_message=message,
            session_id=session_id,
            user_id=request.username
        )
        
        final_text = ""
        for event in events:
            if event.error_message:
                print(f"Agent Error: {event.error_message}")
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text:
                        final_text += part.text
        
        print(f"Successfully generated card for {request.username}")
        return {
            "status": "success",
            "username": request.username,
            "message": final_text,
            "card_url": f"/static/cards/{request.username}.html"
        }
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"Detailed Server Error:\n{error_trace}")
        raise HTTPException(status_code=500, detail=str(e))

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
