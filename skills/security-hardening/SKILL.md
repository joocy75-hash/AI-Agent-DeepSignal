---
name: security-hardening
description: Security hardening workflow for this project. Use when asked to fix or improve auth, rate limiting, admin access controls, OAuth security, or token handling.
metadata:
  short-description: Project security hardening
---

# Security Hardening Workflow

## Scope

Apply this workflow when the user requests security fixes or to address known security issues in the backend or frontend.

## Checklist (use as needed)

1) Authentication and tokens
- Verify JWT validation paths exist and are used consistently.
- Ensure optional auth does not bypass required auth.
- Prefer HttpOnly cookies for tokens when feasible; otherwise document risks.

2) Rate limiting
- Ensure user-level rate limit uses a validated user identifier.
- Verify endpoint-specific limits apply correctly.

3) Admin access controls
- Confirm admin routes match middleware path checks.
- Ensure admin IP restrictions apply to all admin endpoints.

4) OAuth state handling
- Enforce TTL on state values.
- Clean up expired states.
- Use shared storage (Redis) in multi-process deployments when possible.

## Files to inspect

- `backend/src/utils/jwt_auth.py`
- `backend/src/middleware/rate_limit_improved.py`
- `backend/src/middleware/admin_ip_whitelist.py`
- `backend/src/api/oauth.py`
- `frontend/src/context/AuthContext.jsx`
- `admin-frontend/src/context/AuthContext.jsx`

## Changes

Make targeted fixes and keep changes minimal. For larger architectural changes (e.g., cookie-based auth), propose a phased plan before implementing.
