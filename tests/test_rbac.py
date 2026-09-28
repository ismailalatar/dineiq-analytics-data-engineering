def test_protected_requires_auth(client):
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
