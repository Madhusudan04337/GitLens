from fastapi import FastAPI
from pydantic import BaseModel
from .agent import run_agent

app = FastAPI(title="GitHub Dev Card Generator API")

class CardRequest(BaseModel):
    username: str
    theme: str = "default"

@app.post("/generate-card")
async def generate_card(request: CardRequest):
    prompt = f"Generate a dev card for GitHub user {request.username} with theme {request.theme}"
    result = await run_agent(prompt)
    return {"status": "success", "result": result}

@app.get("/health")
def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
