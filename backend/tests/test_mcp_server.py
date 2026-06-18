import pytest
import json
from unittest.mock import patch, MagicMock, AsyncMock
from backend.mcp_server import scrape_github, analyze_profile, generate_card_html, save_card
import os
from pathlib import Path

@pytest.mark.asyncio
@patch("httpx.AsyncClient.get")
async def test_scrape_github_success(mock_get):
    """Test successful GitHub scraping."""
    username = "testuser"
    
    # Mock user profile response
    mock_user_resp = MagicMock()
    mock_user_resp.status_code = 200
    mock_user_resp.json.return_value = {
        "name": "Test User",
        "avatar_url": "https://example.com/avatar.png",
        "bio": "Test Bio",
        "location": "Test Location",
        "public_repos": 10,
        "followers": 100
    }
    
    # Mock repos response
    mock_repos_resp = MagicMock()
    mock_repos_resp.status_code = 200
    mock_repos_resp.json.return_value = [
        {"name": "repo1", "stargazers_count": 50, "language": "Python", "description": "Desc 1", "fork": False},
    ]
    
    mock_get.side_effect = [mock_user_resp, mock_repos_resp]
    
    result = await scrape_github(username)
    
    assert result["name"] == "Test User"
    assert len(result["top_repos"]) == 1
    assert result["top_repos"][0]["name"] == "repo1"

@pytest.mark.asyncio
@patch("backend.mcp_server.model.generate_content")
async def test_analyze_profile_success(mock_gen):
    """Test successful profile analysis via Gemini."""
    mock_response = MagicMock()
    mock_response.text = json.dumps({
        "developer_vibe": "Cool dev.",
        "top_skills": ["Python"],
        "fun_fact": "Likes tests.",
        "card_theme": "hacker"
    })
    mock_gen.return_value = mock_response
    
    github_data = {"public_repos": 5, "top_languages": ["Python"]}
    result = await analyze_profile(github_data)
    
    assert result["developer_vibe"] == "Cool dev."
    assert result["card_theme"] == "hacker"

@pytest.mark.asyncio
async def test_generate_card_html(mock_github_data, mock_analysis_data):
    """Test HTML generation from template."""
    username = "testuser"
    html = await generate_card_html(username, mock_github_data, mock_analysis_data)
    
    assert "<!DOCTYPE html>" in html
    assert username in html
    assert mock_github_data["name"] in html
    assert mock_analysis_data["developer_vibe"] in html

@pytest.mark.asyncio
async def test_save_card():
    """Test saving the generated card to a file."""
    username = "testuser_save"
    html_content = "<html>Test</html>"
    
    # Use a temporary directory for the test
    with patch("backend.mcp_server.Path") as mock_path:
        mock_backend_dir = MagicMock()
        mock_path.return_value.parent.absolute.return_value = mock_backend_dir
        
        mock_cards_dir = MagicMock()
        mock_backend_dir.__truediv__.return_value.__truediv__.return_value = mock_cards_dir
        
        mock_file = MagicMock()
        mock_cards_dir.__truediv__.return_value = mock_file
        
        result = await save_card(username, html_content)
        
        assert f"/static/cards/{username}.html" in result
        mock_file.write_text.assert_called_once_with(html_content, encoding="utf-8")
