from fastapi import FastAPI
from fastapi.testclient import TestClient

from review_summary.routers.summaries import summaries


def test_review_summary_http_endpoint_rejects_missing_mounted_target() -> None:
    app = FastAPI()
    app.include_router(summaries, prefix="/api/v1")

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/review-summaries",
            json={"query": "隔音怎么样？"},
        )

    assert response.status_code == 400
    assert response.json()["detail"] == "A mounted review target is required"
