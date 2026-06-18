FROM python:3.11-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Copy requirements from backend
COPY backend/requirements.txt .
RUN uv pip install --system -r requirements.txt

# Copy all code (backend and frontend)
COPY . .

# Ensure static cards directory exists
RUN mkdir -p backend/static/cards

EXPOSE 8080

# Run the backend which now serves everything
CMD ["python", "backend/main.py"]
