FROM python:3.11-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

COPY requirements.txt .
RUN uv pip install --system -r requirements.txt

# Copy backend code
COPY . .

# Copy frontend code so backend can serve it
COPY ../frontend /app/frontend

EXPOSE 8080

CMD ["python", "main.py"]
