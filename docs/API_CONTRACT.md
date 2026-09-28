# API Contract for 4B and 4C

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
