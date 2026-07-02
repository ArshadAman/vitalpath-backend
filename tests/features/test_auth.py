import pytest

def test_user_registration_and_login(client):
    # 1. Register a new user
    register_payload = {
        "email": "testuser@vitalpath.com",
        "phone_number": "+1234567890",
        "password": "strongpassword123"
    }
    response = client.post("/auth/register", json=register_payload)
    assert response.status_code == 210 or response.status_code == 201
    data = response.json()
    assert data["email"] == "testuser@vitalpath.com"
    assert data["is_active"] is True

    # 2. Try to register with duplicate email
    dup_response = client.post("/auth/register", json=register_payload)
    assert dup_response.status_code == 400
    assert dup_response.json()["detail"] == "Email already registered"

    # 3. Login with correct credentials
    login_payload = {
        "email": "testuser@vitalpath.com",
        "password": "strongpassword123"
    }
    login_response = client.post("/auth/login", json=login_payload)
    assert login_response.status_code == 200
    login_data = login_response.json()
    assert "access_token" in login_data
    assert "refresh_token" in login_data
    assert login_data["token_type"] == "bearer"

    # 3a. Refresh token verification
    refresh_payload = {
        "refresh_token": login_data["refresh_token"]
    }
    refresh_response = client.post("/auth/refresh", json=refresh_payload)
    assert refresh_response.status_code == 200
    refresh_data = refresh_response.json()
    assert "access_token" in refresh_data
    assert "refresh_token" in refresh_data
    assert refresh_data["token_type"] == "bearer"

    # 4. Login with incorrect credentials
    bad_login_payload = {
        "email": "testuser@vitalpath.com",
        "password": "wrongpassword"
    }
    bad_login_response = client.post("/auth/login", json=bad_login_payload)
    assert bad_login_response.status_code == 400

def test_google_oauth2_auth(client):
    # 1. Authenticate new Google user
    google_payload = {
        "id_token": "mock_google_id_token_12345",
        "email": "oauthuser@vitalpath.com",
        "name": "OAuth User"
    }
    response = client.post("/auth/google", json=google_payload)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    
    # 2. Login again with same Google account (verifies it logs in and returns correct tokens)
    login_again_response = client.post("/auth/google", json=google_payload)
    assert login_again_response.status_code == 200
    again_data = login_again_response.json()
    assert "access_token" in again_data
    assert "refresh_token" in again_data
