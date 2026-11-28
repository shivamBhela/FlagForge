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


def test_login_rate_limit_rejects_repeated_bad_passwords(client):
    payload = {
        "email": "throttled.user@flagforge.io",
        "password": "Password123!",
        "full_name": "Throttled User",
    }
    assert client.post("/api/v1/auth/register", json=payload).status_code == 201

    for _ in range(8):
        response = client.post(
            "/api/v1/auth/login",
            json={"email": payload["email"], "password": "incorrect"},
        )
        assert response.status_code == 401

    limited = client.post(
        "/api/v1/auth/login",
        json={"email": payload["email"], "password": "incorrect"},
    )
    assert limited.status_code == 429
    assert int(limited.headers["Retry-After"]) > 0
    assert payload["email"] not in limited.text


def test_login_fails_closed_when_rate_limit_store_is_unavailable(client, monkeypatch):
    from redis.exceptions import RedisError
    from app.core.login_rate_limit import get_login_rate_limit_redis

    class UnavailableRedis:
        async def eval(self, *_args):
            raise RedisError("connection refused")

    async def override_redis():
        yield UnavailableRedis()

    monkeypatch.setitem(client.app.dependency_overrides, get_login_rate_limit_redis, override_redis)
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "user@flagforge.io", "password": "not-a-secret"},
    )
    assert response.status_code == 503
    assert "temporarily unavailable" in response.json()["detail"]


def test_successful_login_clears_account_failure_counter(client):
    payload = {
        "email": "reset.counter@flagforge.io",
        "password": "Password123!",
        "full_name": "Reset Counter",
    }
    assert client.post("/api/v1/auth/register", json=payload).status_code == 201

    for _ in range(7):
        assert client.post(
            "/api/v1/auth/login",
            json={"email": payload["email"], "password": "incorrect"},
        ).status_code == 401

    assert client.post(
        "/api/v1/auth/login",
        json={"email": payload["email"], "password": payload["password"]},
    ).status_code == 200

    for _ in range(8):
        assert client.post(
            "/api/v1/auth/login",
            json={"email": payload["email"], "password": "incorrect"},
        ).status_code == 401
