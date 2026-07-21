import logging
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
from fastapi import APIRouter
import httpx

from config import settings

logger = logging.getLogger(__name__)

router = APIRouter()

BACKEND_URL = settings.BACKEND_TRANSACCIONAL_URL


@router.get("/health")
async def health_check():
    return {"status": "ok", "service": "claimvision-gateway"}


@router.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_to_backend(request: Request, path: str):
    target_url = f"{BACKEND_URL}/api/v1/{path}"

    headers = {}
    for key, value in request.headers.items():
        if key.lower() not in ("host", "transfer-encoding"):
            headers[key] = value

    if settings.GATEWAY_INTERNAL_SECRET:
        headers["X-Gateway-Secret"] = settings.GATEWAY_INTERNAL_SECRET

    try:
        body = await request.body()

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.request(
                method=request.method,
                url=target_url,
                headers=headers,
                content=body,
                params=dict(request.query_params),
            )

        excluded_headers = {
            "content-encoding", "content-length", "transfer-encoding", "connection"
        }
        response_headers = {
            k: v for k, v in response.headers.items()
            if k.lower() not in excluded_headers
        }

        return Response(
            content=response.content,
            status_code=response.status_code,
            headers=response_headers,
        )

    except httpx.ConnectError:
        logger.error("No se pudo conectar al backend: %s", target_url)
        return JSONResponse(
            status_code=502,
            content={"detail": "Backend transaccional no disponible"},
        )
    except httpx.TimeoutException:
        logger.error("Timeout conectando al backend: %s", target_url)
        return JSONResponse(
            status_code=504,
            content={"detail": "Gateway timeout"},
        )
    except Exception as e:
        logger.error("Error en proxy: %s", e)
        return JSONResponse(
            status_code=500,
            content={"detail": "Error interno del gateway"},
        )
