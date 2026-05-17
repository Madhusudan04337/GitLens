import asyncio
import os
import sys
from main import github_card_agent, session_service, memory_service
from google.adk import Runner
from google.genai.types import Content, Part

async def diagnose():
    runner = Runner(
        agent=github_card_agent,
        app_name="Diagnose",
        session_service=session_service,
        memory_service=memory_service,
        auto_create_session=True
    )
    
    username = "torvalds"
    message = Content(
        parts=[Part(text=f"Generate a dev card for {username}")],
        role="user"
    )
    
    print(f"--- Diagnosing Agent for user: {username} ---")
    print(f"MCP Server Path: {os.path.join(os.path.dirname(__file__), 'mcp_server.py')}")
    
    try:
        events = runner.run(
            new_message=message,
            session_id="diag_session",
            user_id="diag_user"
        )
        
        for event in events:
            # Check for content/thoughts
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text:
                        print(f"[Agent]: {part.text}")
            
            # Check for tool calls (actions)
            if event.actions:
                for action in event.actions:
                    print(f"[Action]: Calling tool '{action.tool_call.name}' with args: {action.tool_call.arguments}")
            
            # Check for errors
            if event.error_message:
                print(f"[Error]: {event.error_message}")
                
        print("--- Diagnosis Complete ---")
    except Exception as e:
        print(f"[Fatal Exception]: {e}")

if __name__ == "__main__":
    asyncio.run(diagnose())
