import pytest
from datetime import datetime, timedelta

def test_score_calculation(client):
    # 1. Register a new user
    user_payload = {
        "email": "scoreuser@vitalpath.com",
        "password": "userpass123"
    }
    register_response = client.post("/auth/register", json=user_payload)
    assert register_response.status_code == 201
    user_id = register_response.json()["id"]

    # Authenticate and obtain JWT
    login_payload = {
        "email": "scoreuser@vitalpath.com",
        "password": "userpass123"
    }
    login_response = client.post("/auth/login", json=login_payload)
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Add profile info (Smoking = active to check score reduction)
    profile_payload = {
        "name": "Score Test User",
        "gender": "male",
        "date_of_birth": (datetime.utcnow() - timedelta(days=32*365)).isoformat(), # 32 years old
        "height": 175.0,
        "weight": 80.0,
        "smoking": "active",
        "activity": "rarely"
    }
    profile_response = client.post("/profile", json=profile_payload, headers=headers)
    assert profile_response.status_code == 201

    # 3. Request metrics calculation
    calc_response = client.post("/score/calculate", headers=headers)
    assert calc_response.status_code == 200
    calc_data = calc_response.json()
    
    assert calc_data["user_id"] == user_id
    # Smoking is active and exercise is rarely, score should be less than the base 80
    assert calc_data["score"] < 80
    # Smoking offset (+5) and exercise offset (+2) should make health age higher than actual age (32)
    assert calc_data["health_age"] > 32

    # 4. Read latest score
    latest_response = client.get("/score/latest", headers=headers)
    assert latest_response.status_code == 200
    assert latest_response.json()["score"] == calc_data["score"]
