"""
Query Processing API

FastAPI application for processing RAG queries with vector search and LLM integration.
"""

import os
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging

from app.routes import query
from app.middleware import auth
from app.utils.errors import handle_error

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="My Building Board Query API",
    description="RAG query processing API with vector search and LLM integration",
    version="1.0.0",
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "https://localhost:3000").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global error handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle all unhandled exceptions."""
    return handle_error(exc, request)

# Include routers
app.include_router(query.router, prefix="/api", tags=["query"])

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "service": "query-api"}

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "My Building Board Query API",
        "version": "1.0.0",
        "docs": "/docs",
    }
