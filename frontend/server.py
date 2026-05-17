import os
import http.server
import socketserver

PORT = 80
BACKEND_URL = os.environ.get("BACKEND_URL", "")

# Inject the backend URL into the HTML file
with open("index.html", "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace("__BACKEND_URL__", BACKEND_URL)

with open("index.html", "w", encoding="utf-8") as f:
    f.write(content)

# Start the simple HTTP server
class MyHttpRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Cache-Control', 'no-store, must-revalidate')
        super().end_headers()

Handler = MyHttpRequestHandler
with socketserver.TCPServer(("", PORT), Handler) as httpd:
    print(f"Serving at port {PORT} with BACKEND_URL={BACKEND_URL}")
    httpd.serve_forever()
