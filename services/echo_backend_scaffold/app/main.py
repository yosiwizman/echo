"""Echo Backend - FastAPI Application."""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import chat, health, notes
from app.services.notes_store import NotesStore

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S%z",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler."""
    logger.info("Starting Echo Backend")
    # Initialize notes store
    app.state.notes_store = NotesStore()
    await app.state.notes_store.initialize()
    yield
    logger.info("Shutting down Echo Backend")


app = FastAPI(
    title="Echo Backend",
    description="AI-powered wearable companion backend service",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware for mobile app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router)
app.include_router(chat.router)
app.include_router(notes.router)


@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint."""
    return {"message": "Echo Backend API", "docs": "/docs"}
