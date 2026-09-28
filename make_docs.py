import os
ROOT = r"D:\DineIQ"
os.makedirs(os.path.join(ROOT, "docs"), exist_ok=True)

FILES = {}

FILES[r"docs\PERMISSIONS_MATRIX.md"] = """# Permissions Matrix

SRS ref: §1.6 (FR i–ii)

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

Enforced via @require_permission decorator. Permissions stored in DB.
"""

FILES[r"docs\ERROR_CODES.md"] = """# Error Codes

SRS ref: §1.6 (FR lxiv)

Uniform envelope:
{ "error": { "code": "...", "message": "...", "details": null } }

| HTTP | Code | Description |
|---|---|---|
| 400 | VALIDATION_ERROR | Invalid input |
| 401 | AUTH_UNAUTHORIZED | Missing/invalid token |
| 401 | AUTH_INVALID_CREDENTIALS | Login failed |
| 403 | AUTH_ACCOUNT_LOCKED | Locked after 5 fails |
| 403 | RBAC_PERMISSION_DENIED | Missing permission |
| 404 | RESOURCE_NOT_FOUND | Not found |
| 409 | CONFLICT_DUPLICATE | Duplicate |
| 422 | UNPROCESSABLE_ENTITY | Malformed body |
| 429 | RATE_LIMIT_EXCEEDED | Too many requests |
| 500 | INTERNAL_ERROR | Unhandled |
| 503 | SERVICE_UNAVAILABLE | Analysis/model down |
"""

FILES[r"docs\INFRASTRUCTURE_REPORT.md"] = """# Infrastructure Report - Student 4A

## Scope (SRS §1.6)
- FR i  Registration & Authentication
- FR ii Role-Based Access Control
- FR iii-xi Application Database
- FR lxiii Audit Trail
- FR lxiv Error Handling
- FR lxvi Export

## Stack (SRS §1.9.2)
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
| GET | /api/v1/export/{report}?format=csv|xlsx | export:csv / export:xlsx |

## Security
- bcrypt cost 12
- JWT access 15m + refresh 7d
- Account lock after 5 failed attempts
- Rate limit 10/min on /login
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
Body: {"email": "...", "password": "..."}
Response 200:
{
  "access_token": "...",
  "refresh_token": "...",
  "user": { "id":1, "email":"...", "roles":[...], "permissions":[...] }
}

## Protected calls
Header: Authorization: Bearer <access_token>

## Error envelope
{"error":{"code":"...","message":"...","details":null}}

## Export
GET /export/{report}?format=csv|xlsx
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

## Run