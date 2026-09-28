def test_login_success(client):
    res = client.post("/api/auth/login", json={
        "email": "ajeet.singh@kit.ac.in",
        "password": "password123"
    })
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["user"]["email"] == "ajeet.singh@kit.ac.in"
    assert data["user"]["role"] == "admin"

def test_login_invalid_password(client):
    res = client.post("/api/auth/login", json={
        "email": "ajeet.singh@kit.ac.in",
        "password": "wrongpassword"
    })
    assert res.status_code == 401

def test_get_current_user(client):
    login_res = client.post("/api/auth/login", json={
        "email": "ajeet.singh@kit.ac.in",
        "password": "password123"
    })
    token = login_res.json()["access_token"]
    res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    assert res.json()["full_name"] == "Ajeet Singh"
