# 📇 GitLens: GitHub Dev Card Generator

GitLens is a premium developer identity platform that transforms your GitHub presence into a sleek, AI-powered shareable card. By analyzing your public activity, pinned repositories, and coding habits, GitLens generates a unique "Developer Vibe" and a high-fidelity visual card.

![Premium Card Preview](https://raw.githubusercontent.com/Madhusudan04337/GitLens/main/preview.png) *(Placeholder for your preview image)*

## ✨ Key Features

-   **AI Vibe Analysis:** Uses **Gemini 1.5 Flash** to analyze your profile and generate a creative personality description.
-   **Smart Repository Selection:** Automatically prioritizes your **Pinned Repositories** using the GitHub GraphQL API, falling back to recent repositories if none are pinned.
-   **Premium Themes:** Five distinct visual identities (Hacker, Builder, Researcher, Designer, Open Source Hero) that adapt to your profile data.
-   **High-Fidelity Responsive Design:** Ultra-premium landscape layout for desktop (840x480px) and a seamless, edge-to-edge stacked layout for mobile. Features glassmorphism, fluid typography, and interactive hover states.
-   **Single-Port Deployment:** Simplified architecture where the backend (FastAPI) serves the frontend (React) directly on a single port for maximum reliability.

## 🚀 Tech Stack

-   **Orchestration:** [Google ADK](https://github.com/google/adk)
-   **LLM:** [Gemini 1.5 Flash](https://aistudio.google.com/)
-   **Tooling:** [MCP (FastMCP)](https://modelcontextprotocol.io/)
-   **Backend:** FastAPI (Python 3.11+)
-   **Frontend:** React (Standard JS, Tailwind CSS, Glassmorphism)
-   **APIs:** GitHub REST v3 & GraphQL v4
-   **Dependency Management:** `uv` (preferred)

## 🛠️ Getting Started

### Prerequisites

-   Python 3.11+
-   [uv](https://github.com/astral-sh/uv) installed (or `pip`)
-   A Gemini API Key (Get one at [Google AI Studio](https://aistudio.google.com/))
-   A GitHub Personal Access Token (for Pinned Repositories & GraphQL access)

### Installation & Running

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

3.  **Setup & Run (Using `uv` - Recommended):**
    ```bash
    # Create venv and install dependencies
    uv venv
    source .venv/bin/activate  # On Windows: .venv\Scripts\activate
    uv pip install -r backend/requirements.txt

    # Start the application
    python backend/main.py
    ```

4.  **Setup & Run (Using `pip`):**
    ```bash
    # Install dependencies
    pip install -r backend/requirements.txt

    # Start the application
    python backend/main.py
    ```

5.  **Access the application:**
    Open your browser and navigate to:
    **[http://localhost:8080](http://localhost:8080)**

## 🧪 Running Tests

GitLens includes a comprehensive unit testing suite using `pytest`.

```bash
# Set PYTHONPATH to the backend directory
export PYTHONPATH=$PYTHONPATH:$(pwd)/backend

# Run all tests
pytest backend/tests/ -v
```

## 🎨 Card Themes

-   **Hacker:** Dark neon aesthetics with matrix-inspired glows.
-   **Builder:** Clean, professional blue tones for the modern engineer.
-   **Designer:** Purple gradients and playful layouts for creative devs.
-   **Researcher:** Minimalist, data-focused structure with high readability.
-   **Open Source Hero:** Warm, amber-toned identity for community champions.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

MIT License - Copyright (c) 2026 Madhusudan
