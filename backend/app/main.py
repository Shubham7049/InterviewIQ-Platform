import os
import logging
from contextlib import asynccontextmanager
# InterviewIQ FastAPI Application Entrypoint
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.db.connection import connect_to_mongo, close_mongo_connection
from app.api.interviews import router as interviews_router

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("interviewiq")


def setup_langsmith_tracing():
    """Configures LangSmith tracing if environment variables are provided."""
    if settings.LANGCHAIN_TRACING_V2 and settings.LANGCHAIN_API_KEY:
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGCHAIN_API_KEY"] = settings.LANGCHAIN_API_KEY
        os.environ["LANGCHAIN_PROJECT"] = settings.LANGCHAIN_PROJECT
        logger.info(f"LangSmith tracing enabled for project: {settings.LANGCHAIN_PROJECT}")
    else:
        logger.info("LangSmith tracing is disabled or credentials are not configured.")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for database connection and tracing setup."""
    logger.info("Initializing InterviewIQ backend service...")
    setup_langsmith_tracing()
    await connect_to_mongo()
    yield
    logger.info("Shutting down InterviewIQ backend service...")
    await close_mongo_connection()


app = FastAPI(
    title="InterviewIQ API",
    description="Agentic AI Interview Assessment Platform API powered by LangGraph, Groq, and MongoDB.",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS dynamically from environment/settings
configured_origins = [
    origin.strip()
    for origin in settings.ALLOWED_ORIGINS.split(",")
    if origin.strip()
]
default_origins = [
    "http://localhost:5173",
    "http://localhost:3000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:3000",
]
origins = list(dict.fromkeys(configured_origins + default_origins))

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if "*" in origins else origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(interviews_router)


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "InterviewIQ API",
        "version": "1.0.0",
        "langsmith_tracing": bool(settings.LANGCHAIN_TRACING_V2 and settings.LANGCHAIN_API_KEY),
    }


# Global Exception Handler to avoid leaking internal stack traces
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception on {request.method} {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An unexpected internal server error occurred. Please try again later."},
    )
