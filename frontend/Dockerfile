FROM python:3.11-slim

WORKDIR /app

COPY index.html .

EXPOSE 80

CMD sh -c "if [ -n \"$BACKEND_URL\" ]; then sed -i \"s|__BACKEND_URL__|$BACKEND_URL|g\" index.html; fi && python -m http.server 80"
