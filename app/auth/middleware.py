# app/auth/middleware.py
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import RedirectResponse
from app.auth.auth import get_current_user


class AuthMiddleware(BaseHTTPMiddleware):
    """Middleware to protect routes"""

    def __init__(self, app, excluded_paths=None):
        super().__init__(app)
        self.excluded_paths = excluded_paths or [
            "/",
            "/login",
            "/signup",
            "/token",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/health",
            "/api/health",
        ]

    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        # Skip authentication for excluded paths
        if any(path.startswith(excluded) for excluded in self.excluded_paths):
            return await call_next(request)

        # Check for token in cookie or header
        token = request.cookies.get("access_token")
        if not token:
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]

        if token:
            from app.database.db import SessionLocal
            db = SessionLocal()
            try:
                user = await get_current_user(token, db)
                if user:
                    request.state.user = user
                    return await call_next(request)
            except Exception:
                # Token validation failed, continue to redirect
                pass
            finally:
                db.close()

        # Redirect to login for HTML requests, return 401 for API
        if path.startswith("/api/"):
            return RedirectResponse(url="/login", status_code=401)
        else:
            return RedirectResponse(url="/login", status_code=302)
