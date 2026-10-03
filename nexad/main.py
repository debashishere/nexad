"""nexad/main.py — FastAPI application entry point.

Creates the FastAPI app instance and registers all routers.
Run via: uvicorn nexad.main:app --host 0.0.0.0 --port 8000
"""

import uvicorn
from fastapi import FastAPI

from nexad.gateway.routers.health import router as health_router

app = FastAPI(
    title="NexAd",
    description="Agentic Ad Mediation & Execution Gateway",
    version="0.1.0",
)

app.include_router(health_router)


@app.get("/")
async def root() -> dict:
    """Service identity probe.

    Returns a static JSON payload that confirms the service is running.
    Intentionally does not depend on the database or cache so it responds
    even during early startup.
    """
    return {"service": "nexad", "status": "starting"}


if __name__ == "__main__":
    uvicorn.run("nexad.main:app", host="0.0.0.0", port=8000, reload=False)
