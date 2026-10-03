"""Tests for nexad/main.py — seam S2: GET / root route.

Spec (issue 01):
  GET / returns {"service": "nexad", "status": "starting"} with HTTP 200.

Uses FastAPI's TestClient (via httpx) so no real server is needed.
The app is imported directly; Settings are not loaded (the route doesn't
require config — this is a health/readiness probe that works even before
the DB is up).
"""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def client():
    """Return a TestClient wrapping the NexAd FastAPI app."""
    from nexad.main import app  # noqa: PLC0415

    return TestClient(app)


# ---------------------------------------------------------------------------
# S2-A: GET / returns the expected status payload
# ---------------------------------------------------------------------------


def test_root_returns_service_status(client):
    """GET / responds with HTTP 200 and the service identity JSON."""
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {"service": "nexad", "status": "starting"}
