"""
Health check HTTP server for container orchestrator liveness probes.

Exposes GET /healthz (and /health) returning HTTP 200 with no authentication.
Runs in a background daemon thread so it does not interfere with the crawler.
"""

import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer


class _HealthHandler(BaseHTTPRequestHandler):
    """Minimal HTTP handler that serves /healthz and /health."""

    def do_GET(self):  # noqa: N802
        if self.path in ("/healthz", "/health"):
            body = json.dumps({"status": "ok"}).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):  # noqa: A002
        # Suppress default access logs to keep crawler output clean
        pass


def start_health_server(port: int = 8080) -> HTTPServer:
    """Start the health check server in a background daemon thread.

    Args:
        port: TCP port to listen on (default 8080).

    Returns:
        The running HTTPServer instance.
    """
    server = HTTPServer(("", port), _HealthHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    print(f"Health check server listening on port {port} (/healthz)")
    return server
