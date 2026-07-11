import pytest
from datetime import datetime, timedelta

def test_recommendations_generation(client):
    # 1. Register a new user
    user_payload = {
        "email": "recuser@vitalpath.com",
        "password": "userpass123"
    }
    register_response = client.post("/auth/register", json=user_payload)
    assert register_response.status_code == 201

    # Authenticate and obtain JWT
    login_payload = {
        "email": "recuser@vitalpath.com",
        "password": "userpass123"
    }
    login_response = client.post("/auth/login", json=login_payload)
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Add profile with goal = muscle_gain and diet = vegan
    profile_payload = {
        "name": "Rec Test User",
        "gender": "male",
        "age": 28,
        "height": 180.0,
        "weight": 75.0,
        "healthGoal": "muscle_gain",
        "diet": "vegan",
        "calorieTarget": 2500,
        "waterTarget": 3000
    }
    profile_response = client.post("/profile", json=profile_payload, headers=headers)
    assert profile_response.status_code == 201

    # 3. Fetch recommendations
    rec_response = client.get("/recommendations", headers=headers)
    assert rec_response.status_code == 200
    rec_data = rec_response.json()

    # Validate muscle gain + vegan mappings
    assert rec_data["exercise"]["plan_name"] == "Hypertrophy & Resistance Protocol"
    assert "vegan" in rec_data["nutrition"]["rationale"].lower()
    assert rec_data["nutrition"]["protein_target_g"] == 75.0 * 1.5  # 112.5g (from vegan template factor)
    assert rec_data["nutrition"]["calorie_target_kcal"] == 2500 - 200  # 2300 kcal (from vegan template adjust)
    assert any("tofu" in s.lower() or "tempeh" in s.lower() for s in rec_data["nutrition"]["meal_suggestions"])
