"""Vohrad Backend"""

from fastapi import FastAPI

app = FastAPI(
    title="Vohrad API",
    description="Multi-tenant FastAPI application foundation",
    version="1.0.0",
)


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Welcome to Vohrad API"}


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "vohrad-api"}