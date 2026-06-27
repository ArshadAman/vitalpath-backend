import pytest
from datetime import datetime, timedelta

def test_score_calculation(client):
    # 1. Create a user health profile
    user_payload = {
        "email": "scoreuser@vitalpath.com",
        "password": "userpass123"
    }
    register_response = client.post("/auth/register", json=user_payload)
    user_id = register_response.json()["id"]

    # 2. Add profile info (Smoking = active to check score reduction)
    profile_payload = {
        "name": "Score Test User",
        "gender": "male",
        "date_of_birth": (datetime.utcnow() - timedelta(days=32*365)).isoformat(), # 32 years old
        "height": 175.0,
        "weight": 80.0,
        "smoking_status": "active",
        "exercise_frequency": "rarely"
    }
    client.post(f"/profile?user_id={user_id}", json=profile_payload)

    # 3. Request metrics calculation
    calc_response = client.post(f"/score/calculate?user_id={user_id}")
    assert calc_response.status_code == 200
    calc_data = calc_response.json()
    
    assert calc_data["user_id"] == user_id
    # Smoking is active and exercise is rarely, score should be less than the base 80
    assert calc_data["score"] < 80
    # Smoking offset (+5) and exercise offset (+2) should make health age higher than actual age (32)
    assert calc_data["health_age"] > 32

    # 4. Read latest score
    latest_response = client.get(f"/score/latest?user_id={user_id}")
    assert latest_response.status_code == 200
    assert latest_response.json()["score"] == calc_data["score"]
