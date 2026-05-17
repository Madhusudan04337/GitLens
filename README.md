# 📇 GitLens: GitHub Dev Card Generator

GitLens is a premium developer identity platform that transforms your GitHub presence into a sleek, AI-powered shareable card. By analyzing your public activity, pinned repositories, and coding habits, GitLens generates a unique "Developer Vibe" and a high-fidelity visual card.

![Premium Card Preview](https://raw.githubusercontent.com/Madhusudan04337/GitLens/main/preview.png) *(Placeholder for your preview image)*

## ✨ Key Features

-   **AI Vibe Analysis:** Uses **Gemini 1.5 Flash** to analyze your profile and generate a creative personality description.
-   **Smart Repository Selection:** Automatically prioritizes your **Pinned Repositories** using the GitHub GraphQL API, falling back to recent repositories if none are pinned.
-   **Premium Themes:** Five distinct visual identities (Hacker, Builder, Researcher, Designer, Open Source Hero) that adapt to your profile data.
-   **High-Fidelity Design:** Ultra-premium landscape layout (840x480px) with glassmorphism effects, fluid typography, and interactive hover states.
-   **Shareable Identity:** Generates unique verification IDs and standalone HTML cards perfect for embedding in your portfolio or sharing on social media.

## 🚀 Tech Stack

-   **Orchestration:** [Google ADK](https://github.com/google/adk)
-   **LLM:** [Gemini 2.0 Flash](https://aistudio.google.com/)
-   **Tooling:** [MCP (FastMCP)](https://modelcontextprotocol.io/)
-   **Backend:** FastAPI (Python 3.11+)
-   **Frontend:** React (Tailwind CSS, Glassmorphism)
-   **APIs:** GitHub REST v3 & GraphQL v4
-   **Dependency Management:** `uv` (preferred)

## 🛠️ Getting Started

### Prerequisites

-   Python 3.11+
-   [uv](https://github.com/astral-sh/uv) installed
-   A Gemini API Key
-   A GitHub Personal Access Token (for Pinned Repositories & GraphQL access)

### Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/Madhusudan04337/GitLens.git
    cd GitLens
    ```

2.  **Configure environment variables:**
    Create a `.env` file in the root directory:
    ```env
    GEMINI_API_KEY=your_gemini_api_key
    GITHUB_TOKEN=your_github_pat
    ```

3.  **Run with Docker (Recommended):**
    ```bash
    docker compose up --build
    ```
    -   Frontend: `http://localhost:80`
    -   Backend: `http://localhost:8080`

4.  **Run Locally (Development):**
    ```bash
    # Install dependencies
    uv pip install -r backend/requirements.txt

    # Start the backend
    cd backend
    python main.py
    ```

## 🌐 Live Deployment

The project is currently deployed on Google Cloud Run and can be accessed via the following public URLs:

- **Frontend:** [https://github-card-frontend-143544260816.us-central1.run.app](https://github-card-frontend-143544260816.us-central1.run.app)
- **Backend API:** [https://github-card-backend-143544260816.us-central1.run.app](https://github-card-backend-143544260816.us-central1.run.app)

## 🎨 Card Themes

-   **Hacker:** Dark neon aesthetics with matrix-inspired glows.
-   **Builder:** Clean, professional blue tones for the modern engineer.
-   **Designer:** Purple gradients and playful layouts for creative devs.
-   **Researcher:** Minimalist, data-focused structure with high readability.
-   **Open Source Hero:** Warm, amber-toned identity for community champions.

## 📝 Workflow Mandates

Every generation task follows a strict pipeline:
1.  **Scrape:** Fetches profile data + GraphQL Pinned Repos.
2.  **Analyze:** Gemini processes data for "Vibe" and "Theme".
3.  **Generate:** Crafts the premium HTML/CSS structure.
4.  **Save:** Persists the card to `/static/cards/{username}.html`.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

MIT License - Copyright (c) 2026 Madhusudan
