def test_register_and_me(client):
    response = client.post(
        "/api/auth/register",
        json={"username": "alice", "password": "password123", "email": "alice@example.com"},
    )
    assert response.status_code == 201
    payload = response.get_json()
    assert payload["user"]["username"] == "alice"

    me_response = client.get("/api/auth/me")
    assert me_response.status_code == 200
    assert me_response.get_json()["user"]["username"] == "alice"


def test_login_logout_flow(client):
    client.post("/api/auth/register", json={"username": "bob", "password": "password123"})
    login_response = client.post("/api/auth/login", json={"username": "bob", "password": "password123"})
    assert login_response.status_code == 200

    logout_response = client.post("/api/auth/logout")
    assert logout_response.status_code == 200

