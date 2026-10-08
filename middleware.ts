// Harbour SSO — standard OIDC middleware (deterministic template)
// Reads credentials from process.env — never hardcoded.

import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

// ─── Configuration (from env — never secrets in source) ──────────────────────

const OIDC_ISSUER = process.env.OIDC_ISSUER;
const OIDC_CLIENT_ID = process.env.OIDC_CLIENT_ID;
const OIDC_CLIENT_SECRET = process.env.OIDC_CLIENT_SECRET;

if (!OIDC_ISSUER || !OIDC_CLIENT_ID || !OIDC_CLIENT_SECRET) {
  throw new Error(
    "Missing OIDC environment variables. Set OIDC_ISSUER, OIDC_CLIENT_ID, and OIDC_CLIENT_SECRET."
  );
}

// ─── Public paths that do NOT require authentication ────────────────────────

const PUBLIC_PATHS = ["/healthz", "/_next", "/favicon.ico"];

function isPublicPath(pathname: string): boolean {
  return PUBLIC_PATHS.some((p) => pathname === p || pathname.startsWith(p + "/"));
}

// ─── OIDC helper ─────────────────────────────────────────────────────────────

function getAuthUrl(request: NextRequest): string {
  const params = new URLSearchParams({
    response_type: "code",
    client_id: OIDC_CLIENT_ID,
    scope: "openid profile email",
    redirect_uri: new URL("/api/auth/callback", request.url).toString(),
    state: crypto.randomUUID(),
  });
  return `${OIDC_ISSUER}/authorize?${params.toString()}`;
}

// ─── Token validation via OIDC introspection ────────────────────────────────

// Module-level cache: populated on first successful OIDC discovery fetch.
let _introspectionEndpoint: string | null = null;

async function getIntrospectionEndpoint(): Promise<string> {
  if (_introspectionEndpoint) return _introspectionEndpoint;
  const discoveryUrl = `${OIDC_ISSUER}/.well-known/openid-configuration`;
  const res = await fetch(discoveryUrl);
  if (!res.ok) {
    throw new Error(`OIDC discovery failed with HTTP ${res.status}`);
  }
  const cfg = (await res.json()) as { introspection_endpoint?: string };
  if (!cfg.introspection_endpoint) {
    throw new Error("OIDC discovery document is missing introspection_endpoint");
  }
  _introspectionEndpoint = cfg.introspection_endpoint;
  return _introspectionEndpoint;
}

/**
 * Validates a session token against the IdP's introspection endpoint.
 * Returns true only when the IdP confirms the token is active.
 */
async function validateSessionToken(token: string): Promise<boolean> {
  try {
    const endpoint = await getIntrospectionEndpoint();
    const credentials = btoa(`${OIDC_CLIENT_ID}:${OIDC_CLIENT_SECRET}`);
    const response = await fetch(endpoint, {
      method: "POST",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
        Authorization: `Basic ${credentials}`,
      },
      body: new URLSearchParams({
        token,
        token_type_hint: "access_token",
      }).toString(),
    });
    if (!response.ok) return false;
    const data = (await response.json()) as { active?: boolean };
    return data.active === true;
  } catch {
    // Treat any validation error (network, parse, etc.) as invalid.
    return false;
  }
}

// ─── Middleware ─────────────────────────────────────────────────────────────

export async function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Allow public paths through without authentication
  if (isPublicPath(pathname)) {
    return NextResponse.next();
  }

  // Check for a session token in the HttpOnly cookie
  const sessionToken = request.cookies.get("session_token")?.value;

  if (!sessionToken) {
    // No token present — redirect to IdP for authentication
    const authUrl = getAuthUrl(request);
    return NextResponse.redirect(authUrl);
  }

  // Validate session_token against the IdP introspection endpoint.
  // Any token not confirmed active by the IdP is rejected with a redirect.
  const isValid = await validateSessionToken(sessionToken);
  if (!isValid) {
    const authUrl = getAuthUrl(request);
    return NextResponse.redirect(authUrl);
  }

  return NextResponse.next();
}

// Only run middleware on application routes, not static assets
export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico|.*\.png$).*)"],
};
