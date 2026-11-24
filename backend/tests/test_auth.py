def test_user_registration_and_login(client):
    # 1. Register new user
    reg_payload = {
        "email": "sarah.connor@flagforge.io",
        "password": "Password123!",
        "full_name": "Sarah Connor",
    }
    res = client.post("/api/v1/auth/register", json=reg_payload)
    assert res.status_code == 201
    user_data = res.json()
    assert user_data["email"] == "sarah.connor@flagforge.io"
    assert user_data["full_name"] == "Sarah Connor"
    assert "id" in user_data

    # 2. Reject duplicate registration
    res_dup = client.post("/api/v1/auth/register", json=reg_payload)
    assert res_dup.status_code == 400
    assert "already exists" in res_dup.json()["detail"]

    # 3. Reject login with bad password
    res_bad = client.post("/api/v1/auth/login", json={"email": "sarah.connor@flagforge.io", "password": "WrongPassword"})
    assert res_bad.status_code == 401

    # 4. Login with correct password
    res_login = client.post("/api/v1/auth/login", json={"email": "sarah.connor@flagforge.io", "password": "Password123!"})
    assert res_login.status_code == 200
    tokens = res_login.json()
    assert "access_token" in tokens
    assert "refresh_token" in tokens
    assert tokens["token_type"] == "bearer"

    # 5. Access profile with token
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    res_me = client.get("/api/v1/auth/me", headers=headers)
    assert res_me.status_code == 200
    assert res_me.json()["email"] == "sarah.connor@flagforge.io"

    # 6. Reject profile access without token
    res_unauth = client.get("/api/v1/auth/me")
    assert res_unauth.status_code == 401

    # 7. Refresh token flow
    res_refresh = client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert res_refresh.status_code == 200
    new_tokens = res_refresh.json()
    assert "access_token" in new_tokens
    assert new_tokens["access_token"] != tokens["access_token"]

    # 8. Access profile with new access token
    headers_new = {"Authorization": f"Bearer {new_tokens['access_token']}"}
    res_me_new = client.get("/api/v1/auth/me", headers=headers_new)
    assert res_me_new.status_code == 200
    assert res_me_new.json()["email"] == "sarah.connor@flagforge.io"

    # 9. Logout
    res_logout = client.post("/api/v1/auth/logout", headers=headers_new)
    assert res_logout.status_code == 200
    assert res_logout.json()["status"] == "ok"
