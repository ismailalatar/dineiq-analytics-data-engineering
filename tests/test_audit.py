def test_audit_requires_auth(client):
    assert client.get("/api/v1/audit").status_code == 401

def test_audit_records_login(client, auth_headers):
    r = client.get("/api/v1/audit?limit=50", headers=auth_headers)
    assert r.status_code == 200
