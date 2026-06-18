import pytest
from fastapi.testclient import TestClient
from backend.main import app

@pytest.fixture
def client():
    """FastAPI test client fixture."""
    return TestClient(app)

@pytest.fixture
def mock_github_data():
    """Fixture for mock GitHub data."""
    return {
        "name": "Test User",
        "avatar_url": "https://example.com/avatar.png",
        "bio": "Test Bio",
        "location": "Test Location",
        "public_repos": 10,
        "followers": 100,
        "top_repos": [
            {"name": "repo1", "stars": 50, "language": "Python", "description": "Desc 1"},
            {"name": "repo2", "stars": 30, "language": "JavaScript", "description": "Desc 2"},
        ],
        "top_languages": ["Python", "JavaScript"],
        "repos_type": "Recent Repositories"
    }

@pytest.fixture
def mock_analysis_data():
    """Fixture for mock analysis data."""
    return {
        "developer_vibe": "A brilliant test developer.",
        "top_skills": ["Testing", "Pytest"],
        "fun_fact": "This developer never has bugs.",
        "card_theme": "hacker"
    }
