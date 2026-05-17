import asyncio
import json
import os
from mcp_server import scrape_github, analyze_profile, generate_card_html, save_card
from dotenv import load_dotenv

load_dotenv()

async def test_flow():
    username = "torvalds"
    print(f"--- Testing for user: {username} ---")
    
    # 1. Scrape
    print("Step 1: Scraping GitHub...")
    github_data = await scrape_github(username)
    if "error" in github_data:
        print(f"Error in scrape_github: {github_data['error']}")
        return

    # 2. Analyze
    print("Step 2: Analyzing profile with Gemini...")
    try:
        analysis = await analyze_profile(github_data)
        print(f"Analysis complete.")
        print(f"Developer Vibe: {analysis.get('developer_vibe')}")
        print(f"Card Theme: {analysis.get('card_theme')}")
    except Exception as e:
        print(f"Error in analyze_profile: {str(e)}")
        return

    # 3. Generate HTML
    print("Step 3: Generating HTML card...")
    try:
        html = await generate_card_html(username, github_data, analysis)
        print("HTML generated successfully.")
    except Exception as e:
        print(f"Error in generate_card_html: {str(e)}")
        return

    # 4. Save (Bonus verification)
    print("Step 4: Saving card...")
    try:
        path = await save_card(username, html)
        print(f"Card saved to: {path}")
    except Exception as e:
        print(f"Error in save_card: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_flow())
