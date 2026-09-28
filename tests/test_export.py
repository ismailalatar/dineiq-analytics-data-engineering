def test_export_requires_auth(client):
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
