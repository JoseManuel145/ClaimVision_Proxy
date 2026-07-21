import time
import logging
from collections import defaultdict
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from config import settings

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, default_limit: str = "60/minute"):
        super().__init__(app)
        self._parse_limit(default_limit)
        self._requests: dict[str, list[float]] = defaultdict(list)

    def _parse_limit(self, limit_str: str) -> None:
        count, period = limit_str.split("/")
        self._max_requests = int(count)
        self._window_seconds = {
            "second": 1,
            "minute": 60,
            "hour": 3600,
            "day": 86400,
        }.get(period, 60)

    def _get_client_ip(self, request: Request) -> str:
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    async def dispatch(self, request: Request, call_next):
        if request.url.path == "/health":
            return await call_next(request)

        client_ip = self._get_client_ip(request)
        now = time.time()

        self._requests[client_ip] = [
            t for t in self._requests[client_ip]
            if now - t < self._window_seconds
        ]

        if len(self._requests[client_ip]) >= self._max_requests:
            logger.warning("Rate limit excedido para IP: %s", client_ip)
            return JSONResponse(
                status_code=429,
                content={"detail": "Demasiadas peticiones. Intenta de nuevo más tarde."},
                headers={"Retry-After": str(self._window_seconds)},
            )

        self._requests[client_ip].append(now)
        return await call_next(request)


class DDoSProtectionMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, max_burst: int = 30, burst_window: int = 10):
        super().__init__(app)
        self._max_burst = max_burst
        self._burst_window = burst_window
        self._hits: dict[str, list[float]] = defaultdict(list)
        self._blocked: dict[str, float] = {}

    def _get_client_ip(self, request: Request) -> str:
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    async def dispatch(self, request: Request, call_next):
        client_ip = self._get_client_ip(request)
        now = time.time()

        if client_ip in settings.BLOCKED_IPS:
            return JSONResponse(status_code=403, content={"detail": "Acceso denegado"})

        if client_ip in self._blocked:
            if now - self._blocked[client_ip] < 300:
                return JSONResponse(
                    status_code=429,
                    content={"detail": "IP temporalmente bloqueada por actividad sospechosa"},
                    headers={"Retry-After": "300"},
                )
            del self._blocked[client_ip]

        self._hits[client_ip] = [
            t for t in self._hits[client_ip]
            if now - t < self._burst_window
        ]

        if len(self._hits[client_ip]) >= self._max_burst:
            self._blocked[client_ip] = now
            self._hits[client_ip].clear()
            logger.warning("IP bloqueada por burst de requests: %s", client_ip)
            return JSONResponse(
                status_code=429,
                content={"detail": "IP bloqueada temporalmente por actividad sospechosa"},
                headers={"Retry-After": "300"},
            )

        self._hits[client_ip].append(now)
        return await call_next(request)


class RequestSanitizationMiddleware(BaseHTTPMiddleware):
    BLOCKED_PATTERNS = [
        "../", "..\\", "%2e%2e", "%252e",
        "<script", "javascript:", "onerror=",
        "UNION SELECT", "DROP TABLE", "--",
        "\x00",
    ]

    async def dispatch(self, request: Request, call_next):
        full_url = str(request.url).lower()
        for pattern in self.BLOCKED_PATTERNS:
            if pattern.lower() in full_url:
                logger.warning("Request bloqueado por patrón sospechoso: %s from %s",
                               pattern, request.client.host if request.client else "unknown")
                return JSONResponse(
                    status_code=400,
                    content={"detail": "Solicitud inválida"},
                )

        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > settings.MAX_REQUEST_SIZE:
            return JSONResponse(
                status_code=413,
                content={"detail": "Payload demasiado grande"},
            )

        return await call_next(request)
