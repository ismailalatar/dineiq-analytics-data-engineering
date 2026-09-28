import os
ROOT = r"D:\DineIQ\tests"
os.makedirs(ROOT, exist_ok=True)

files = {
"conftest.py": """import pytest
from app import create_app
from app.extensions import db as _db
from app.models.rbac import User, Role, Permission

@pytest.fixture
def app():
    app = create_app()
    app.config.update(TESTING=True, SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
                      JWT_SECRET_KEY="test-secret-key-long-enough-for-hs256-testing-32b")
    with app.app_context():
        _db.create_all()
        for code in ["export:csv","export:xlsx","audit:read","users:read","locations:read","locations:write"]:
            _db.session.add(Permission(code=code))
        _db.session.commit()
        admin_role = Role(name="administrator")
        admin_role.permissions = Permission.query.all()
        _db.session.add(admin_role); _db.session.commit()
        u = User(email="test@dineiq.local", username="tester", full_name="Tester")
        u.set_password("Test@12345")
        u.roles = [admin_role]
        _db.session.add(u); _db.session.commit()
        yield app
        _db.session.remove(); _db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def admin_token(client):
    r = client.post("/api/v1/auth/login", json={"email":"test@dineiq.local","password":"Test@12345"})
    return r.get_json()["access_token"]

@pytest.fixture
def auth_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}
""",
"test_auth.py": """def test_health(client):
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
""",
"test_rbac.py": """def test_protected_requires_auth(client):
    assert client.get("/api/v1/locations").status_code == 401

def test_admin_can_list_locations(client, auth_headers):
    r = client.get("/api/v1/locations", headers=auth_headers)
    assert r.status_code == 200

def test_admin_can_create_location(client, auth_headers):
    r = client.post("/api/v1/locations", headers=auth_headers, json={"code":"LOC01","name":"Main"})
    assert r.status_code == 201

def test_permission_denied(client, app):
    from app.models.rbac import User, Role, Permission
    from app.extensions import db
    with app.app_context():
        role = Role(name="viewer_only")
        role.permissions = [Permission.query.filter_by(code="users:read").first()]
        db.session.add(role); db.session.commit()
        u = User(email="v@d.local", username="v")
        u.set_password("Viewer@123")
        u.roles = [role]
        db.session.add(u); db.session.commit()
    r = client.post("/api/v1/auth/login", json={"email":"v@d.local","password":"Viewer@123"})
    token = r.get_json()["access_token"]
    r2 = client.post("/api/v1/locations", headers={"Authorization": f"Bearer {token}"}, json={"code":"X","name":"X"})
    assert r2.status_code == 403
""",
"test_export.py": """def test_export_requires_auth(client):
    assert client.get("/api/v1/export/locations").status_code == 401

def test_export_csv(client, auth_headers):
    r = client.get("/api/v1/export/locations?format=csv", headers=auth_headers)
    assert r.status_code == 200
    assert "text/csv" in r.headers["Content-Type"]

def test_export_xlsx(client, auth_headers):
    r = client.get("/api/v1/export/locations?format=xlsx", headers=auth_headers)
    assert r.status_code == 200

def test_export_unknown(client, auth_headers):
    assert client.get("/api/v1/export/nope?format=csv", headers=auth_headers).status_code == 404

def test_export_bad_format(client, auth_headers):
    assert client.get("/api/v1/export/locations?format=pdf", headers=auth_headers).status_code == 400
""",
"test_audit.py": """def test_audit_requires_auth(client):
    assert client.get("/api/v1/audit").status_code == 401

def test_audit_records_login(client, auth_headers):
    r = client.get("/api/v1/audit?limit=50", headers=auth_headers)
    assert r.status_code == 200
""",
"__init__.py": ""
}

for name, content in files.items():
    with open(os.path.join(ROOT, name), "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  created: tests/{name}")
print("DONE tests")