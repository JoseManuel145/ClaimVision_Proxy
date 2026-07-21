import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from middleware.security import (
    RateLimitMiddleware,
    DDoSProtectionMiddleware,
    RequestSanitizationMiddleware,
)
from middleware.headers import SecurityHeadersMiddleware
from router import router

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="ClaimVision API Gateway",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
)

app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RateLimitMiddleware, default_limit=settings.RATE_LIMIT_DEFAULT)
app.add_middleware(DDoSProtectionMiddleware, max_burst=30, burst_window=10)
app.add_middleware(RequestSanitizationMiddleware)

app.include_router(router)


@app.on_event("startup")
async def startup():
    logger.info("ClaimVision Gateway iniciado en modo %s", settings.ENVIRONMENT)
    logger.info("Backend: %s", settings.BACKEND_TRANSACCIONAL_URL)


@app.on_event("shutdown")
async def shutdown():
    logger.info("ClaimVision Gateway apagado")
