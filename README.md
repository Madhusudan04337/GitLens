# 📇 GitLens: GitHub Dev Card Generator

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688.svg)](https://fastapi.tiangolo.com/)
[![Google ADK](https://img.shields.io/badge/Google_ADK-Enabled-4285F4.svg)](https://github.com/google/adk)
[![MCP](https://img.shields.io/badge/MCP-FastMCP-FF6F00.svg)](https://modelcontextprotocol.io/)

GitLens is a premium developer identity platform that transforms your GitHub presence into a sleek, AI-powered shareable card. By analyzing public activity, pinned repositories, and coding patterns, GitLens synthesizes a unique "Developer Vibe" and renders a high-fidelity visual developer card.

---

## 📸 Preview

![GitLens Preview](https://raw.githubusercontent.com/Madhusudan04337/GitLens/main/preview.png)

---

## ✨ Key Features

- **🤖 AI Developer Vibe Analysis:** Uses **Gemini 1.5 Flash** to analyze profile repositories, language distributions, and commit metrics to generate a creative developer persona.
- **📌 Smart Repository Selection:** Leverages GitHub's GraphQL v4 API to extract pinned repositories, gracefully falling back to top starred and active public repositories.
- **🛡️ Resilience & Dual-Mode Execution:** Employs **Google ADK** (Agent Development Kit) agent orchestration with automated fallback to manual tool orchestration if LLM rate limits or network issues occur.
- **🎨 5 Distinct Themes:** Offers visual identities tailored to developer styles (Hacker, Builder, Researcher, Designer, Open Source Hero).
- **📱 Responsive & Glassmorphic UI:** High-density landscape card for desktop viewports and adaptive stacked layout for mobile devices, featuring glassmorphism and subtle glowing animations.
- **🚀 Unified Single-Port Deployment:** Serves both FastAPI backend endpoints and the React frontend on a unified port (`8080`), simplifying Cloud Run container hosting.
- **⚡ Powered by `uv`:** Optimized dependency management and fast installation.

---

## 🚀 Tech Stack

| Component | Technology | Description |
| :--- | :--- | :--- |
| **Agent Orchestration** | [Google ADK](https://github.com/google/adk) | Agent execution lifecycle & session state service |
| **Tool Protocol** | [FastMCP](https://modelcontextprotocol.io/) | Model Context Protocol servers exposing modular developer tools |
| **LLM Engine** | [Gemini 1.5 Flash](https://aistudio.google.com/) | AI model powering profile analysis & vibe classification |
| **Backend API** | FastAPI + Uvicorn | Async ASGI backend handling REST routes & static file hosting |
| **Frontend UI** | React + Tailwind CSS | Single-page UI with dynamic animated AI loading states |
| **GitHub APIs** | REST v3 & GraphQL v4 | User profile fetching, star statistics & pinned repo queries |
| **Package Manager** | `uv` / `pip` | High-performance Python environment setup |
| **Deployment** | Docker & Google Cloud Run | Containerized deployment configuration |

---

## 📁 Repository Structure

```
GitLens/
├── backend/
│   ├── agent.py               # Google ADK agent configuration & runner setup
│   ├── main.py                # FastAPI web app, static routes & fallback orchestration
│   ├── mcp_server.py          # FastMCP tools (scraping, AI analysis, card rendering)
│   ├── requirements.txt       # Python backend dependencies
│   ├── static/
│   │   └── cards/             # Generated user card HTML storage
│   ├── templates/
│   │   └── card_template.html # Jinja2 HTML template for dev cards
│   └── tests/
│       ├── test_api.py        # FastAPI endpoint unit tests
│       └── test_mcp_server.py # MCP tools unit tests
├── frontend/
│   ├── index.html             # React single-page application frontend
│   ├── server.py              # Standalone development frontend server
│   └── requirements.txt       # Frontend server dependencies
├── Dockerfile                 # Multi-stage production container Dockerfile
├── docker-compose.yml         # Compose configuration for container orchestration
├── GEMINI.md                  # Project rules & architecture guidelines
└── README.md                  # Comprehensive project documentation
```

---

## 🛠️ Prerequisites & Setup

### Requirements
- **Python 3.11+**
- **uv** (Recommended: `curl -LsSf https://astral.sh/uv/install.sh | sh`) or standard `pip`
- **Docker** (Optional, for containerized run)

### Environment Variables
Create a `.env` file in the root directory:

```env
# Gemini API Key (Required for AI Vibe Analysis)
GEMINI_API_KEY=your_gemini_api_key_here

# GitHub Personal Access Token (Recommended to access GraphQL & pinned repos)
GITHUB_TOKEN=your_github_pat_here
```

---

## 🚀 Running the Application

### Option 1: Unified Server (Recommended)

Serves the backend API and frontend together on port `8080`:

1. **Install backend dependencies:**
   ```bash
   uv pip install -r backend/requirements.txt
   # OR
   pip install -r backend/requirements.txt
   ```

2. **Start the server:**
   ```bash
   uvicorn backend.main:app --host 0.0.0.0 --port 8080 --reload
   # OR
   python backend/main.py
   ```

3. **Open application:**
   Navigate to **[http://localhost:8080](http://localhost:8080)** in your browser.

---

### Option 2: Docker & Docker Compose

To launch the full containerized environment:

```bash
docker-compose up --build
```
Access the application at **[http://localhost:8080](http://localhost:8080)**.

---

### Option 3: Google Cloud Run

Deploy directly to Google Cloud Run using the included `Dockerfile`:

```bash
# Build image using Cloud Build
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/gitlens:latest

# Deploy container to Cloud Run
gcloud run deploy gitlens \
  --image gcr.io/YOUR_PROJECT_ID/gitlens:latest \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars GEMINI_API_KEY="your_key",GITHUB_TOKEN="your_token"
```

---

## 📡 API Reference

### `POST /generate`
Generates a developer card for the specified GitHub username.

- **Request Payload:**
  ```json
  {
    "username": "octocat"
  }
  ```
- **Response:**
  ```json
  {
    "status": "success",
    "username": "octocat",
    "card_url": "/static/cards/octocat.html"
  }
  ```

### `GET /card/{username}`
Serves the rendered HTML card for a specific user.

### `GET /health`
Health check endpoint for deployment monitoring.

---

## 🧪 Running Tests

Execute unit and integration tests using `pytest`:

```bash
# Set python path to backend directory
export PYTHONPATH=$PYTHONPATH:$(pwd)/backend

# Run tests
pytest backend/tests/ -v
```

---

## 🎨 Theme Overview

- 🟩 **Hacker:** Neon green highlights and matrix-inspired dark aesthetics.
- 🟦 **Builder:** Minimalist corporate blue design for modern software engineers.
- 🟪 **Designer:** Creative purple-to-pink gradients with fluid typography.
- ⬜ **Researcher:** Clean monochromatic interface emphasizing data readability.
- 🟧 **Open Source Hero:** Warm golden glow celebrating open-source contributions.

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
