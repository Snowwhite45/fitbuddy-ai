import os

os.environ["GEMINI_API_KEY"] = ""

from fastapi.testclient import TestClient

from app.database import Base, engine
from app.main import app

Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

client = TestClient(app)


def test_homepage():
    response = client.get("/")
    assert response.status_code == 200
    assert "FitBuddy" in response.text
    assert "Generate 7-Day Plan" in response.text


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_generate_and_feedback():
    payload = {
        "username": "Test User",
        "user_id": "TEST001",
        "age": 25,
        "weight": 70,
        "goal": "muscle gain",
        "intensity": "medium",
    }

    response = client.post("/api/generate-workout", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == "TEST001"
    assert len(data["plan"]["days"]) == 7
    assert data["nutrition_tip"]

    feedback = client.post(
        "/api/submit-feedback",
        json={
            "user_id": "TEST001",
            "feedback": "Add more mobility and make the first day easier.",
        },
    )
    assert feedback.status_code == 200
    assert len(feedback.json()["plan"]["days"]) == 7


def test_admin_view():
    response = client.get("/view-all-users")
    assert response.status_code == 200
    assert "Test User" in response.text


def test_delete_user():
    response = client.post("/delete-user/TEST001", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/view-all-users"
