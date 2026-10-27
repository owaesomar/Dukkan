import logging
import re
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from redis.exceptions import RedisError
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from starlette.middleware.base import RequestResponseEndpoint
from starlette.responses import Response

from app.common.exceptions import DomainError
from app.core.config import get_settings
from app.core.logging import configure_logging, request_id_context
from app.core.rate_limit import _redis
from app.db.dependencies import SessionDep
from app.db.session import engine
from app.modules.analytics.router import router as analytics_router
from app.modules.auth.router import router as auth_router
from app.modules.catalog.router import router as catalog_router
from app.modules.inventory.router import router as inventory_router
from app.modules.memberships.router import router as memberships_router
from app.modules.orders.router import router as orders_router
from app.modules.platform_admin.router import router as platform_admin_router
from app.modules.storefront.router import directory_router as public_store_directory_router
from app.modules.storefront.router import router as storefront_router
from app.modules.stores.router import router as stores_router
from app.modules.subscriptions.router import router as subscriptions_router


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    configure_logging(settings.log_level)
    try:
        yield
    finally:
        engine.dispose()


settings = get_settings()
app = FastAPI(title="Dukkan API", version="0.6.0", lifespan=lifespan)
logger = logging.getLogger(__name__)


@app.exception_handler(DomainError)
async def domain_error_handler(_: Request, exc: DomainError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


@app.exception_handler(RequestValidationError)
async def validation_error_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    safe_errors = [
        {key: value for key, value in error.items() if key not in {"input", "ctx"}}
        for error in exc.errors()
    ]
    return JSONResponse(status_code=422, content={"detail": safe_errors})


@app.exception_handler(Exception)
async def internal_error_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error(
        "Unhandled request error",
        exc_info=(type(exc), exc, exc.__traceback__),
        extra={"path": request.url.path},
    )
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


@app.middleware("http")
async def request_context_middleware(
    request: Request, call_next: RequestResponseEndpoint
) -> Response:
    provided_id = request.headers.get("X-Request-ID", "")
    request_id = provided_id if re.fullmatch(r"[A-Za-z0-9._-]{1,64}", provided_id) else uuid4().hex
    context_token = request_id_context.set(request_id)
    try:
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response
    finally:
        request_id_context.reset(context_token)


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=[
        "Authorization",
        "Content-Type",
        "Idempotency-Key",
        "X-Order-Tracking-Token",
        "X-Request-ID",
        "X-CSRF-Token",
    ],
)
app.include_router(auth_router, prefix="/api/v1")
app.include_router(stores_router, prefix="/api/v1")
app.include_router(memberships_router, prefix="/api/v1")
app.include_router(catalog_router, prefix="/api/v1")
app.include_router(inventory_router, prefix="/api/v1")
app.include_router(orders_router, prefix="/api/v1")
app.include_router(analytics_router, prefix="/api/v1")
app.include_router(subscriptions_router, prefix="/api/v1")
app.include_router(platform_admin_router, prefix="/api/v1")
app.include_router(public_store_directory_router, prefix="/api/v1")
app.include_router(storefront_router, prefix="/api/v1")


@app.get("/health/live", tags=["health"])
def liveness() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/health/ready", tags=["health"])
def readiness(db: SessionDep) -> dict[str, str]:
    try:
        db.execute(text("SELECT 1"))
        _redis().ping()
    except (SQLAlchemyError, RedisError):
        logger.exception("Readiness dependency check failed")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service dependencies are unavailable",
        ) from None
    return {"status": "ready"}
