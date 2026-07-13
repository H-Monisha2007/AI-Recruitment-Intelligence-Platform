"""
FastAPI application entry point — Production-Grade AI Recruitment Intelligence Platform.
"""
from __future__ import annotations
import time
import uuid
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from prometheus_fastapi_instrumentator import Instrumentator

from app.api.v1.api import api_router
from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.core.logging_config import get_logger, request_id_var, setup_logging

# Setup structured logging
setup_logging()
logger = get_logger(__name__)

# ── Rate limiter ──────────────────────────────────────────────────────────────
limiter = Limiter(key_func=get_remote_address, default_limits=[f"{settings.RATE_LIMIT_REQUESTS}/minute"])

# ── Lifespan ──────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing %s v%s in %s mode", settings.APP_NAME, settings.APP_VERSION, settings.ENVIRONMENT)
    
    # Warm up semantic models
    try:
        from app.services.ml_service import _get_sentence_model
        _get_sentence_model()
        logger.info("Semantic models warmed up")
    except Exception as e:
        logger.error("Failed to warm up models: %s", e)
        
    logger.info("Startup sequence complete")
    yield
    logger.info("Shutdown sequence initiated")

# ── App Instance ──────────────────────────────────────────────────────────────
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Enterprise-level AI Recruitment Platform with Semantic Matching and Scalable Background Processing.",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# ── Prometheus Instrumentation ───────────────────────────────────────────────
Instrumentator().instrument(app).expose(app)

# ── Middleware ────────────────────────────────────────────────────────────────
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.middleware("http")
async def request_context_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    token = request_id_var.set(request_id)
    start_time = time.perf_counter()
    
    try:
        response = await call_next(request)
    except Exception as exc:
        logger.exception("Internal Server Error: %s", exc)
        response = JSONResponse(status_code=500, content={"detail": "Internal Server Error"})
    finally:
        process_time = (time.perf_counter() - start_time) * 1000
        logger.info(
            "%s %s | Status: %s | Latency: %.2fms",
            request.method, request.url.path, response.status_code, process_time
        )
        request_id_var.reset(token)
        
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time-Ms"] = f"{process_time:.2f}"
    return response

# ── Exception Handlers ────────────────────────────────────────────────────────
register_exception_handlers(app)

# ── Routes ────────────────────────────────────────────────────────────────────
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/health", tags=["health"])
async def health_check():
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "uptime": "TODO"
    }

@app.get("/", include_in_schema=False)
def root():
    return {"message": f"Welcome to {settings.APP_NAME} API. Visit /docs for documentation."}
