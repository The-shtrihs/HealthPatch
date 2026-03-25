# app/middleware/rate_limit.py
from collections.abc import Callable

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from src.repositories.rate_limit import RateLimitRepository


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, repo_factory: Callable[[], RateLimitRepository], limit: int = 60, window: int = 60):
        super().__init__(app)
        self.repo_factory = repo_factory
        self.limit = limit
        self.window = window

    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host if request.client else "unknown"

        repo = self.repo_factory()

        result = await repo.check(
            identifier=f"ip:{client_ip}",
            limit=self.limit,
            window=self.window,
        )

        response_headers = {
            "X-RateLimit-Limit": str(result.limit),
            "X-RateLimit-Remaining": str(result.remaining),
            "X-RateLimit-Reset": str(result.reset_at),
        }

        if not result.allowed:
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Too Many Requests",
                    "retry_after": result.retry_after,
                },
                headers={
                    **response_headers,
                    "Retry-After": str(result.retry_after),
                },
            )

        response = await call_next(request)

        for key, value in response_headers.items():
            response.headers[key] = value

        return response
