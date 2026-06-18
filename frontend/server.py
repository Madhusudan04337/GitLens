import os
import http.server
import socketserver
from pathlib import Path
from dotenv import load_dotenv

# Find .env in project root
project_root = Path(__file__).parent.parent.absolute()
load_dotenv(project_root / ".env")

PORT = 3000
BACKEND_URL = os.environ.get("BACKEND_URL", "")

# Load the template once
with open("index.html", "r", encoding="utf-8") as f:
    TEMPLATE_CONTENT = f.read()

# Start the simple HTTP server
class MyHttpRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/" or self.path == "/index.html":
            content = TEMPLATE_CONTENT.replace("__BACKEND_URL__", BACKEND_URL)
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.send_header("Cache-Control", "no-store, must-revalidate")
            self.send_header("Content-Length", len(content.encode('utf-8')))
            self.end_headers()
            self.wfile.write(content.encode('utf-8'))
        else:
            super().do_GET()

    def end_headers(self):
        self.send_header('Cache-Control', 'no-store, must-revalidate')
        super().end_headers()

Handler = MyHttpRequestHandler
with socketserver.TCPServer(("", PORT), Handler) as httpd:
    print(f"Serving at port {PORT} with BACKEND_URL={BACKEND_URL}")
    httpd.serve_forever()
