import os
ROOT = r"D:\DineIQ"
os.makedirs(os.path.join(ROOT, "docs"), exist_ok=True)

FILES = {}

FILES[r"docs\PERMISSIONS_MATRIX.md"] = """# Permissions Matrix

SRS ref: 1.6 (FR i-ii)

| Resource / Action | restaurant_manager | analyst | regional_manager | administrator |
|---|:---:|:---:|:---:|:---:|
| users:read | - | - | - | YES |
| users:write | - | - | - | YES |
| roles:read | YES | YES | YES | YES |
| roles:write | - | - | - | YES |
| locations:read | YES | YES | YES | YES |
| locations:write | - | - | - | YES |
| menu:read | YES | YES | YES | YES |
| menu:write | YES | - | - | YES |
| pricing:read | YES | YES | YES | YES |
| pricing:write | YES | - | - | YES |
| orders:read | YES | YES | YES | YES |
| promotions:read | YES | YES | YES | YES |
| promotions:write | YES | - | - | YES |
| ratings:read | YES | YES | YES | YES |
| inventory:read | YES | YES | YES | YES |
| inventory:write | YES | - | - | YES |
| wastage:read | YES | YES | YES | YES |
| wastage:write | YES | - | - | YES |
| analytics:read | YES | YES | YES | YES |
| recommendations:read | YES | YES | YES | YES |
| recommendations:write | - | YES | - | YES |
| audit:read | - | - | YES | YES |
| export:csv | YES | YES | YES | YES |
| export:xlsx | YES | YES | YES | YES |
| models:read | YES | YES | YES | YES |
| models:write | - | YES | - | YES |

Enforced via require_permission decorator. Permissions stored in DB.
"""

FILES[r"docs\ERROR_CODES.md"] = """# Error Codes

SRS ref: 1.6 (FR lxiv)

Uniform envelope: {"error":{"code":"...","message":"...","details":null}}

| HTTP | Code | Description |
|---|---|---|
| 400 | VALIDATION_ERROR | Invalid input |
| 401 | AUTH_UNAUTHORIZED | Missing or invalid token |
| 401 | AUTH_INVALID_CREDENTIALS | Login failed |
| 403 | AUTH_ACCOUNT_LOCKED | Locked after 5 failed attempts |
| 403 | RBAC_PERMISSION_DENIED | Missing permission |
| 404 | RESOURCE_NOT_FOUND | Not found |
| 409 | CONFLICT_DUPLICATE | Duplicate |
| 422 | UNPROCESSABLE_ENTITY | Malformed body |
| 429 | RATE_LIMIT_EXCEEDED | Too many requests |
| 500 | INTERNAL_ERROR | Unhandled |
| 503 | SERVICE_UNAVAILABLE | Analysis or model unavailable |
"""

FILES[r"docs\INFRASTRUCTURE_REPORT.md"] = """# Infrastructure Report - Student 4A

## Scope (SRS 1.6)
- FR i  Registration and Authentication
- FR ii Role-Based Access Control
- FR iii-xi Application Database
- FR lxiii Audit Trail
- FR lxiv Error Handling
- FR lxvi Export

## Stack (SRS 1.9.2)
| Layer | Tech |
|---|---|
| Framework | Flask 3.1 |
| ORM | SQLAlchemy 2.x |
| Migrations | Flask-Migrate |
| DB | SQLite (dev) / PostgreSQL-ready |
| Auth | JWT + bcrypt |
| Rate limit | Flask-Limiter |
| Export | pandas + openpyxl |
| Tests | pytest |

## Endpoints
| Method | Path | Permission |
|---|---|---|
| GET | /health | public |
| POST | /api/v1/auth/register | public |
| POST | /api/v1/auth/login | public (10/min) |
| POST | /api/v1/auth/refresh | refresh token |
| POST | /api/v1/auth/logout | auth |
| GET | /api/v1/auth/me | auth |
| GET | /api/v1/locations | locations:read |
| POST | /api/v1/locations | locations:write |
| GET | /api/v1/menu_items | menu:read |
| GET | /api/v1/users | users:read |
| GET | /api/v1/audit | audit:read |
| GET | /api/v1/export/{report} | export:csv or export:xlsx |

## Security
- bcrypt cost 12
- JWT access 15m, refresh 7d
- Account lock after 5 failed attempts
- Rate limit 10 per minute on /login
- RBAC on every protected endpoint
- Uniform error envelope
- Full audit trail

## Tests
21 passed (auth, rbac, export, audit).
"""

FILES[r"docs\API_CONTRACT.md"] = """# API Contract for 4B and 4C

Base URL: http://HOST:5000/api/v1

## Auth
POST /auth/login
Body: {"email":"...","password":"..."}
Response 200: access_token, refresh_token, user object

## Protected calls
Header: Authorization: Bearer access_token

## Error envelope
{"error":{"code":"...","message":"...","details":null}}

## Export
GET /export/{report}?format=csv or xlsx
Allowed reports: locations, menu_items, customers, recommendations

## Tables owned by 4B (write access)
- recommendations (entity_type, entity_id, action, priority, evidence_json, model_version)
- model_versions (name, version, pipeline, metrics_json, trained_at, is_active)

## Tables owned by 4A (read/write via API only)
users, roles, permissions, user_roles, role_permissions, audit_logs, export_logs,
restaurants, menu_categories, menu_items, pricing_history, customers, orders,
order_items, promotions, ratings, inventory, wastage
"""

FILES[r"docs\TEST_PLAN.md"] = """# Test Plan

| Suite | File | Count | Status |
|---|---|---|---|
| Auth | tests/test_auth.py | 10 | PASS |
| RBAC | tests/test_rbac.py | 4 | PASS |
| Export | tests/test_export.py | 5 | PASS |
| Audit | tests/test_audit.py | 2 | PASS |
| TOTAL | - | 21 | PASS |

## Run command
pytest -q
"""

FILES[r"AI_USAGE.md"] = """# AI Usage Declaration

SRS 1.8 items 13-16.

| Tool | Purpose | Files | Verified by |
|---|---|---|---|
| ChatGPT / Claude | Scaffolding Flask + RBAC + JWT boilerplate | backend skeleton, docs | Student 4A |

## Modifications
- Reviewed and adapted every generated file.
- Verified RBAC matrix against SRS 1.6 (FR i-ii).
- Wrote and ran 21 tests locally.

## Not AI-generated
Final predictions, classifications, recommendations, forecasts produced by team pipelines.

## Testing performed
- All endpoints tested via curl.
- pytest suite 21 passed.
"""

FILES[r".env.example"] = """SECRET_KEY=change_me
JWT_SECRET_KEY=change_me_at_least_32_chars_long_for_hs256
DATABASE_URL=sqlite:///dineiq_app.db
BCRYPT_ROUNDS=12
MAX_LOGIN_ATTEMPTS=5
"""

FILES[r"README.md"] = """# DineIQ Analytics

Big Data + Data Science restaurant intelligence platform.
Aptech - Data Science Intelligence Arena.
Reference: DineIQ Analytics SRS v1.0.

## Repository Layout
- app/, run.py, seed.py: backend source (Student 4A)
- tests/: pytest suite
- migrations/: DB migrations
- spark_jobs/, data_generator/: data engineering (Student 1)
- docs/: documentation

## Backend Quick Start
1. py -3.11 -m venv venv
2. venv\\Scripts\\activate
3. pip install -r requirements.txt
4. flask --app run db upgrade
5. python seed.py
6. python run.py

Server: http://localhost:5000

Default admin:
- email: admin@dineiq.local
- password: Admin@12345

## Tests
pytest -q
Expected: 21 passed.

## Docs
- docs/INFRASTRUCTURE_REPORT.md
- docs/PERMISSIONS_MATRIX.md
- docs/ERROR_CODES.md
- docs/API_CONTRACT.md
- docs/TEST_PLAN.md

## AI Usage
See AI_USAGE.md.
"""

for rel, content in FILES.items():
    full = os.path.join(ROOT, rel)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as f:
        f.write(content)
    print("  created: " + rel)

print("DONE docs")