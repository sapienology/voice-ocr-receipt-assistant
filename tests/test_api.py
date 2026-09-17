from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_root():

    response = client.get("/")

    assert response.status_code == 200

    assert "Voice OCR Receipt Assistant" in response.text


def test_api_root():

    response = client.get("/api")

    assert response.status_code == 200
    assert "API is running" in response.json()["message"]


def test_health():

    response = client.get("/health")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "healthy"


def test_ask_total():

    response = client.post(
        "/ask",
        params={
            "question": "What is the total?"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["success"] is True