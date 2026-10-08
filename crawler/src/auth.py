"""
OIDC authentication dependency for FastAPI routes.

Uses the IdP's token introspection endpoint (discovered via the standard
/.well-known/openid-configuration URL) to validate Bearer tokens on every
request.  Unauthenticated or invalid requests receive HTTP 401.

Usage — protect a route:
    from auth import require_auth

    @router.get("/protected-data", dependencies=[Depends(require_auth)])
    def protected():
        ...

Public routes (e.g. /healthz) should NOT include this dependency.
"""

import os
from base64 import b64encode

import requests as _http
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

# ── OIDC configuration — read from environment, never hardcoded ──────────────

_OIDC_ISSUER = os.environ.get("OIDC_ISSUER", "")
_OIDC_CLIENT_ID = os.environ.get("OIDC_CLIENT_ID", "")
_OIDC_CLIENT_SECRET = os.environ.get("OIDC_CLIENT_SECRET", "")

# ── Module-level cache for the introspection endpoint URL ────────────────────

_introspection_endpoint: str = ""

_bearer_scheme = HTTPBearer(auto_error=True)


def _get_introspection_endpoint() -> str:
    """
    Discover and cache the OIDC token introspection endpoint URL.
    Fetches the IdP's OpenID Connect discovery document on first call.
    """
    global _introspection_endpoint
    if _introspection_endpoint:
        return _introspection_endpoint
    if not _OIDC_ISSUER:
        raise RuntimeError(
            "OIDC_ISSUER environment variable is not set. "
            "Cannot perform token introspection."
        )
    discovery_url = f"{_OIDC_ISSUER}/.well-known/openid-configuration"
    resp = _http.get(discovery_url, timeout=10)
    resp.raise_for_status()
    cfg = resp.json()
    endpoint = cfg.get("introspection_endpoint")
    if not endpoint:
        raise RuntimeError(
            "OIDC discovery document does not contain introspection_endpoint"
        )
    _introspection_endpoint = endpoint
    return _introspection_endpoint


def require_auth(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme),
) -> dict:
    """
    FastAPI dependency that validates a Bearer token via OIDC introspection.

    - Returns the introspection response payload on success.
    - Raises HTTP 401 if the token is absent, inactive, or the IdP
      cannot be reached.

    Apply to any route that serves non-public data:
        @router.get("/data", dependencies=[Depends(require_auth)])
    """
    token = credentials.credentials
    try:
        endpoint = _get_introspection_endpoint()
        b64_creds = b64encode(
            f"{_OIDC_CLIENT_ID}:{_OIDC_CLIENT_SECRET}".encode()
        ).decode()
        resp = _http.post(
            endpoint,
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "Authorization": f"Basic {b64_creds}",
            },
            data={"token": token, "token_type_hint": "access_token"},
            timeout=10,
        )
        if not resp.ok:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token introspection request failed",
                headers={"WWW-Authenticate": "Bearer"},
            )
        payload: dict = resp.json()
        if not payload.get("active"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token is not active",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return payload
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication error: {exc}",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
