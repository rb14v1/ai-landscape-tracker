"""
FastAPI application entry point.

/healthz is intentionally public (used by container orchestrators and
load-balancer liveness probes — no authentication required).

All routes that serve non-public data must declare the require_auth
dependency so unauthenticated requests receive HTTP 401:

    from crawler.src.auth import require_auth
    from fastapi import Depends

    @protected_router.get("/data", dependencies=[Depends(require_auth)])
    def get_data():
        ...
"""

import sys
import os

# Allow imports from crawler/src when running from the repo root.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "crawler", "src"))

from fastapi import APIRouter, FastAPI  # noqa: E402

# ── FastAPI application ──────────────────────────────────────────────────────

app = FastAPI(title="Agentic AI Tracker API")

# ── Public router — no authentication required ───────────────────────────────

router = APIRouter()


@router.get("/healthz")
def healthz():
    """Liveness probe — always public, returns HTTP 200 when the app is up."""
    return {"status": "ok"}


app.include_router(router)

# ── Protected routes must import and use require_auth ────────────────────────
# Example:
#   from auth import require_auth
#   from fastapi import Depends
#
#   @app.get("/api/entries", dependencies=[Depends(require_auth)])
#   def list_entries():
#       ...
