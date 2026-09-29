import pytest
from app import create_app
from app.extensions import db as _db
from app.models.rbac import User, Role, Permission

@pytest.fixture
def app():
    app = create_app(overrides={
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "JWT_SECRET_KEY": "test-secret-key-long-enough-for-hs256-testing-32b",
        "RATELIMIT_ENABLED": False,
    })
    with app.app_context():
        _db.create_all()
        for code in ["export:csv","export:xlsx","audit:read","users:read",
                     "locations:read","locations:write"]:
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
        _db.session.remove()
        _db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def admin_token(client):
    r = client.post("/api/v1/auth/login",
                    json={"email":"test@dineiq.local","password":"Test@12345"})
    return r.get_json()["access_token"]

@pytest.fixture
def auth_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}
from tests.data_fixtures import raw, parquet, clean  # noqa: F401 (Student 6)
