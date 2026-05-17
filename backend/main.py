import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from google.adk import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.memory import InMemoryMemoryService
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

# Ensure static directory exists
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
CARDS_DIR = os.path.join(STATIC_DIR, "cards")
os.makedirs(CARDS_DIR, exist_ok=True)

# Mount static files to serve cards
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Initialize ADK Services and Runner
session_service = InMemorySessionService()
memory_service = InMemoryMemoryService()
runner = Runner(
    agent=github_card_agent,
    app_name="GitHubCardGenerator",
    session_service=session_service,
    memory_service=memory_service
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
    message = f"Generate a dev card for {request.username}"
    
    try:
        # Run the agent via the ADK Runner
        # The runner returns a synchronous generator of events
        events = runner.run(
            new_message=message,
            session_id=session_id,
            user_id=request.username
        )
        
        final_text = ""
        for event in events:
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text:
                        final_text += part.text
        
        # The final result should be the path returned by save_card tool
        return {
            "status": "success",
            "username": request.username,
            "message": final_text,
            "card_url": f"/static/cards/{request.username}.html"
        }
    except Exception as e:
        import traceback
        print(traceback.format_exc())
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
