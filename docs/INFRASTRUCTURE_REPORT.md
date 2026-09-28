# Infrastructure Report - Student 4A

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
