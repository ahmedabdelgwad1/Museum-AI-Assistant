"""FastAPI application entry point."""

import logging
import sys
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.responses import JSONResponse

from app.config import settings
from app.api.middleware import RequestLoggingMiddleware, setup_cors
from app.api.routes.chat import router as chat_router
from app.api.routes.voice import router as voice_router
from app.api.routes.artifacts import router as artifacts_router
from app.models import HealthResponse
from app.rag.vectorstore import collection_count

# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# App lifespan (startup / shutdown)
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Run startup and shutdown logic."""
    logger.info("=== Bibliotheca Alexandrina Museum RAG API Starting ===")

    # Pre-load the embedding model to avoid cold start on first request
    try:
        from app.rag.embedder import get_embedder
        get_embedder()
    except Exception as exc:
        logger.warning("Embedding model pre-load skipped: %s", exc)

    # Log ChromaDB status
    try:
        count = collection_count()
        logger.info("ChromaDB collection has %d artifacts indexed.", count)
        if count == 0:
            logger.warning("Collection is empty! Running auto-indexing...")
            from scripts.index_artifacts import main as index_main
            index_main()
            logger.info("Auto-indexing complete!")
    except Exception as exc:
        logger.warning("ChromaDB status check failed: %s", exc)

    logger.info("API ready. Listening on http://%s:%d", settings.api_host, settings.api_port)
    yield
    logger.info("=== Museum RAG API Shutting Down ===")


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Bibliotheca Alexandrina Museum RAG API",
    description=(
        "Agentic RAG chatbot for the Bibliotheca Alexandrina Antiquities Museum. "
        "Supports Arabic and English queries via text and voice."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Middleware
app.add_middleware(RequestLoggingMiddleware)
setup_cors(app, settings.cors_origins)

# Routers
app.include_router(chat_router)
app.include_router(voice_router)
app.include_router(artifacts_router)


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

@app.get("/health", response_model=HealthResponse, tags=["system"])
async def health_check() -> HealthResponse:
    """Health check endpoint."""
    components = {}

    # Check ChromaDB
    try:
        count = collection_count()
        components["chromadb"] = f"ok ({count} artifacts)"
    except Exception as exc:
        components["chromadb"] = f"error: {exc}"

    # Check Groq client
    try:
        from groq import Groq
        Groq(api_key=settings.groq_api_key)
        components["groq"] = "ok"
    except Exception as exc:
        components["groq"] = f"error: {exc}"

    # Check embedding model
    try:
        from app.rag.embedder import get_embedder
        get_embedder()
        components["embedder"] = "ok"
    except Exception as exc:
        components["embedder"] = f"error: {exc}"

    overall = "healthy" if all("error" not in v for v in components.values()) else "degraded"

    return HealthResponse(
        status=overall,
        version="1.0.0",
        components=components,
    )


@app.get("/", tags=["system"])
async def root():
    """Root endpoint with API info."""
    return JSONResponse(
        content={
            "name": "Bibliotheca Alexandrina Museum RAG API",
            "version": "1.0.0",
            "docs": "/docs",
            "health": "/health",
        }
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True,
        log_level="info",
    )
