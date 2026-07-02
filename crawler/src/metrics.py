"""
Prometheus metrics for the AI Tracker crawler.

Exposes a /metrics endpoint (text/plain; version=0.0.4) on the configured
port (default 8000, override via METRICS_PORT env var).  The HTTP server
runs in a background daemon thread started by calling start_metrics_server().
"""

import os

from prometheus_client import Counter, Histogram, Gauge, start_http_server

# ---------------------------------------------------------------------------
# Metric definitions
# ---------------------------------------------------------------------------

# Total outbound HTTP requests labelled by method and HTTP status code
http_requests_total = Counter(
    'crawler_http_requests_total',
    'Total HTTP requests made by the crawler',
    ['method', 'status'],
)

# Request latency histogram – supports p50/p95/p99 Prometheus queries
http_request_duration_seconds = Histogram(
    'crawler_http_request_duration_seconds',
    'Duration of outbound HTTP requests in seconds',
    buckets=(0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, float('inf')),
)

# Total HTTP errors (non-2xx responses and network/connection failures)
http_errors_total = Counter(
    'crawler_http_errors_total',
    'Total HTTP errors encountered by the crawler',
    ['error_type'],
)

# Number of currently active (in-flight) HTTP connections
active_connections = Gauge(
    'crawler_active_connections',
    'Number of currently active HTTP connections',
)


# ---------------------------------------------------------------------------
# Server startup
# ---------------------------------------------------------------------------

def start_metrics_server(port: int = None) -> None:
    """Start the Prometheus metrics HTTP server.

    prometheus_client.start_http_server() spawns a background daemon thread
    and returns immediately, so the crawler's main execution is unaffected.
    """
    if port is None:
        port = int(os.environ.get('METRICS_PORT', '8000'))
    start_http_server(port)
    print(f"Prometheus /metrics available on port {port}")
