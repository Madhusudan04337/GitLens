import pytest
from unittest.mock import patch, MagicMock
import os

def test_health_check(client):
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "github-dev-card-api"}

def test_root_endpoint(client):
    """Test the root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert "GitLens Backend API is running!" in response.json()["message"]

@patch("backend.main.runner.run")
@patch("backend.main.CARDS_DIR", "/tmp/gitlens_tests/cards")
def test_generate_card_agent_success(mock_run, client):
    """Test successful card generation via agent."""
    username = "testuser"
    os.makedirs("/tmp/gitlens_tests/cards", exist_ok=True)
    card_path = f"/tmp/gitlens_tests/cards/{username}.html"
    with open(card_path, "w") as f:
        f.write("<html>Test Card</html>")
    
    # Mock runner.run to be an empty generator (events consumed)
    mock_run.return_value = iter([])
    
    response = client.post("/generate", json={"username": username})
    
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    assert response.json()["username"] == username
    assert response.json()["card_url"] == f"/static/cards/{username}.html"
    
    # Cleanup
    if os.path.exists(card_path):
        os.remove(card_path)

@patch("backend.main.runner.run")
@patch("backend.main.scrape_github")
@patch("backend.main.analyze_profile")
@patch("backend.main.generate_card_html")
@patch("backend.main.save_card")
def test_generate_card_manual_fallback_success(mock_save, mock_html, mock_analyze, mock_scrape, mock_run, client, mock_github_data, mock_analysis_data):
    """Test successful card generation via manual fallback when agent fails."""
    username = "testuser"
    
    # Force agent failure
    mock_run.side_effect = Exception("Agent failed")
    
    # Mock manual tools
    mock_scrape.return_value = mock_github_data
    mock_analyze.return_value = mock_analysis_data
    mock_html.return_value = "<html>Manual Card</html>"
    mock_save.return_value = f"/static/cards/{username}.html"
    
    response = client.post("/generate", json={"username": username})
    
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    assert response.json()["card_url"] == f"/static/cards/{username}.html"

def test_get_card_not_found(client):
    """Test getting a non-existent card."""
    response = client.get("/card/nonexistentuser")
    assert response.status_code == 404
    assert response.json()["detail"] == "Card not found"
