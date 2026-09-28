def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200

def test_register_success(client):
    r = client.post("/api/v1/auth/register", json={"email":"n@d.local","username":"nu","password":"Pass@12345"})
    assert r.status_code == 201

def test_register_missing_fields(client):
    r = client.post("/api/v1/auth/register", json={"email":"x@x.com"})
    assert r.status_code == 400

def test_register_short_password(client):
    r = client.post("/api/v1/auth/register", json={"email":"s@d.local","username":"sp","password":"abc"})
    assert r.status_code == 400

def test_register_duplicate_email(client):
    p = {"email":"dup@d.local","username":"d1","password":"Pass@12345"}
    client.post("/api/v1/auth/register", json=p)
    r = client.post("/api/v1/auth/register", json={**p,"username":"d2"})
    assert r.status_code == 409

def test_login_success(client):
    r = client.post("/api/v1/auth/login", json={"email":"test@dineiq.local","password":"Test@12345"})
    assert r.status_code == 200
    assert "access_token" in r.get_json()

def test_login_wrong_password(client):
    r = client.post("/api/v1/auth/login", json={"email":"test@dineiq.local","password":"Wrong"})
    assert r.status_code == 401

def test_me_without_token(client):
    assert client.get("/api/v1/auth/me").status_code == 401

def test_me_with_token(client, auth_headers):
    r = client.get("/api/v1/auth/me", headers=auth_headers)
    assert r.status_code == 200
    assert r.get_json()["username"] == "tester"

def test_refresh(client):
    r = client.post("/api/v1/auth/login", json={"email":"test@dineiq.local","password":"Test@12345"})
    refresh = r.get_json()["refresh_token"]
    r2 = client.post("/api/v1/auth/refresh", headers={"Authorization": f"Bearer {refresh}"})
    assert r2.status_code == 200
