FROM python:3.11-slim

WORKDIR /app

COPY index.html .

EXPOSE 80

CMD ["python", "-m", "http.server", "80"]
