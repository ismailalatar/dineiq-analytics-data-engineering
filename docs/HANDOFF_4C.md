# HANDOFF 4C - Frontend & Presentation

Authored by Student 4A. SRS v1.0 reference.

## 1. Backend Status
- Running on: http://localhost:5000
- Auth: JWT (Bearer token)
- RBAC: enforced on every endpoint
- 21 tests passed
- 4B outputs imported: 367 rows across 7 tables

## 2. Login Flow

Step 1 - POST /api/v1/auth/login
Body:
    {"email": "admin@dineiq.local", "password": "Admin@12345"}

Response 200:
    {
      "access_token": "eyJ...",
      "refresh_token": "eyJ...",
      "user": {
        "id": 1,
        "email": "admin@dineiq.local",
        "username": "admin",
        "roles": ["administrator"],
        "permissions": ["analytics:read", "recommendations:read", ...]
      }
    }

Step 2 - Store access_token. Send in header:
    Authorization: Bearer <access_token>

Step 3 - When access_token expires (15 min), call POST /api/v1/auth/refresh with refresh_token.

## 3. Default Accounts

| Role | Email | Password | Created by |
|---|---|---|---|
| Administrator | admin@dineiq.local | Admin@12345 | seed.py |
| Restaurant Manager | create via /auth/register then assign role in DB | - | admin |
| Analyst | same | - | admin |
| Regional Manager | same | - | admin |

## 4. All Endpoints for 4C

### Auth
| Method | Path | Permission | Purpose |
|---|---|---|---|
| POST | /api/v1/auth/register | public | Register |
| POST | /api/v1/auth/login | public (10/min) | Login |
| POST | /api/v1/auth/refresh | refresh token | New access token |
| POST | /api/v1/auth/logout | auth | Logout |
| GET  | /api/v1/auth/me | auth | Current user |

### Reference data
| Method | Path | Permission | Purpose |
|---|---|---|---|
| GET | /api/v1/locations | locations:read | List restaurants |
| POST | /api/v1/locations | locations:write | Create |
| GET | /api/v1/menu_items | menu:read | List menu items |
| GET | /api/v1/users | users:read | List users |

### 4B Analytics Outputs
| Method | Path | Permission | Rows |
|---|---|---|---|
| GET | /api/v1/analytics/summary | analytics:read | counts |
| GET | /api/v1/analytics/recommendations | recommendations:read | 25 |
| GET | /api/v1/analytics/dual_pipeline?limit=100 | analytics:read | 100 |
| GET | /api/v1/analytics/slow_moving | analytics:read | 74 |
| GET | /api/v1/analytics/location_intelligence | analytics:read | 150 |
| GET | /api/v1/analytics/channel_intelligence | analytics:read | 5 |
| GET | /api/v1/analytics/what_if | analytics:read | 8 |
| GET | /api/v1/analytics/surprise_readiness | analytics:read | 5 |

### Audit
| Method | Path | Permission |
|---|---|---|
| GET | /api/v1/audit?limit=100 | audit:read |

### Export
| Method | Path | Permission |
|---|---|---|
| GET | /api/v1/export/{report}?format=csv or xlsx | export:csv / export:xlsx |

Allowed report names:
locations, menu_items, customers, recommendations, dual_pipeline,
slow_moving, location_intelligence, channel_intelligence, what_if,
surprise_readiness

## 5. Response Shapes

### analytics/summary
    {
      "recommendations_count": 25,
      "dual_pipeline_count": 100,
      "slow_moving_count": 74,
      "location_intelligence_count": 150,
      "channel_intelligence_count": 5,
      "what_if_count": 8,
      "surprise_readiness_count": 5
    }

### analytics/recommendations (array)
    [
      {
        "id": 1,
        "finding": "Slow-moving menu item",
        "evidence": "Sales level is Low; quantity sold=552.0, revenue=4003.77",
        "action": "Review demand and menu placement before increasing production.",
        "priority": "Medium",
        "source": "menu_performance_classification",
        "menu_item_id": "148.0",
        "item_name": null
      }
    ]

### analytics/dual_pipeline (array)
    [
      {
        "id": 1,
        "date": "2024-09-23",
        "time_index": 267,
        "actual": 41635.13,
        "order_count": 165,
        "python_prediction": 59159.49,
        "spark_prediction": null,
        "diff": null,
        "error_pct": null,
        "match": 0,
        "explanation": "spark pending"
      }
    ]

### analytics/slow_moving (array)
    [
      {
        "id": 1,
        "menu_item_id": "148",
        "item_name": null,
        "category_name": null,
        "quantity_sold": 552.0,
        "revenue": 4003.77,
        "profit_pct": 0.677499,
        "wastage_pct": 3.005545,
        "promotion_dependency": 0.259058,
        "performance_class": "Low Performer",
        "finding": "Slow-moving menu item",
        "evidence": "...",
        "action": "...",
        "priority": "Medium"
      }
    ]

### analytics/location_intelligence (array)
    [
      {
        "id": 1,
        "menu_item_id": "103",
        "item_name": "Shakshuka",
        "location_count": 20,
        "max_location_quantity": 4374.0,
        "min_location_quantity": 128.0,
        "location_gap": 4246.0,
        "location_ratio": 34.171875,
        "quantity_sold": 26342.0,
        "revenue": 2976845.66,
        "case_type": "Different performance across locations",
        "finding": "...",
        "evidence": "...",
        "action": "...",
        "priority": "High"
      }
    ]

### analytics/channel_intelligence (array)
    [
      {
        "id": 1,
        "preferred_channel": "Dine-in",
        "customers": 15330,
        "orders": 38337,
        "revenue": 9777218.87,
        "avg_order_value": 240.424875,
        "avg_basket_size": 10.043530,
        "avg_recency": 101.816699,
        "finding": "...",
        "evidence": "...",
        "action": "...",
        "priority": "Medium"
      }
    ]

### analytics/what_if (array)
    [
      {
        "id": 1,
        "scenario": "Price Increase",
        "assumption": "Increase menu price by 10%, assume demand decreases by 5%.",
        "estimate_flag": "ESTIMATE - NOT ACTUAL RESULT",
        "menu_item_id": "13",
        "item_name": "Grilled Salmon",
        "baseline_demand": 37314.0,
        "estimated_demand": 35448.30,
        "baseline_revenue": 6089004.91,
        "estimated_revenue": 6363010.13,
        "revenue_change": 274005.22,
        "contribution_margin_change": 5642025.09,
        "demand_change": -1865.70
      }
    ]

### analytics/surprise_readiness (array)
    [
      {
        "id": 1,
        "modification": "Profit threshold",
        "parameter": "PROFIT_THRESHOLD",
        "current_value": "0.2",
        "status": "READY"
      }
    ]

## 6. Error Envelope

All errors return:
    {
      "error": {
        "code": "RBAC_PERMISSION_DENIED",
        "message": "Missing permission: export:csv",
        "details": null
      }
    }

HTTP codes:
- 400 VALIDATION_ERROR
- 401 AUTH_UNAUTHORIZED / AUTH_INVALID_CREDENTIALS
- 403 RBAC_PERMISSION_DENIED / AUTH_ACCOUNT_LOCKED
- 404 RESOURCE_NOT_FOUND
- 409 CONFLICT_DUPLICATE
- 429 RATE_LIMIT_EXCEEDED
- 500 INTERNAL_ERROR

## 7. Required Dashboards (SRS ref)

### 7.1 Executive Dashboard (SRS Step 42)
Data needed:
- Total revenue -> SUM from channel_intelligence.revenue
- Total orders -> SUM from channel_intelligence.orders
- Total customers -> SUM from channel_intelligence.customers
- Average order value -> weighted avg
- Active customers -> SUM channel_intelligence.customers
- Recommendations count -> analytics/summary
- Critical recommendations -> filter recommendations where priority=Critical
- Anomalies -> currently from recommendations (source=anomaly)

Endpoints to use:
- GET /api/v1/analytics/summary
- GET /api/v1/analytics/channel_intelligence
- GET /api/v1/analytics/recommendations

### 7.2 Menu Intelligence Dashboard (SRS Step 43)
Data needed:
- Slow-moving items -> analytics/slow_moving
- Performance classes -> count from slow_moving.performance_class
- Ratings, margins, wastage -> columns in slow_moving
- Profit/Volume/Hidden/Low classification -> from slow_moving.performance_class

Endpoints:
- GET /api/v1/analytics/slow_moving

### 7.3 Customer Intelligence Dashboard (SRS Step 44)
Data needed:
- Customer segments -> channel_intelligence gives channel distribution
- Promotion-sensitive customers -> from channel + recommendation evidence
- High-value customers -> derived from avg_order_value

Endpoints:
- GET /api/v1/analytics/channel_intelligence

### 7.4 Wastage Dashboard (SRS Step 45)
Data needed:
- High-wastage items -> filter slow_moving where wastage_pct is high
- High-wastage locations -> location_intelligence where revenue differs

Endpoints:
- GET /api/v1/analytics/slow_moving (filter wastage_pct)
- GET /api/v1/analytics/location_intelligence

### 7.5 Forecast Dashboard (SRS Step 46)
Data needed:
- Historical vs predicted -> dual_pipeline.actual vs predictions
- Match status, error_pct

Endpoints:
- GET /api/v1/analytics/dual_pipeline?limit=500

Note: The current dual_pipeline output has spark_prediction = null
("spark pending"). When Student 2 fills it, dashboard will show both lines.

### 7.6 Dual-Pipeline Comparison Dashboard (SRS Step 47)
Data needed:
- Spark vs Python predictions
- Match status, differences, agreement percentage

Endpoints:
- GET /api/v1/analytics/dual_pipeline?limit=100

## 8. Filters (SRS Step 48)
Supported via query parameters:
- Date range: not yet - needs extension
- Location: /analytics/location_intelligence filter client-side by menu_item_id
- Menu item: same
- Category: same
- Customer segment: channel_intelligence by preferred_channel
- Channel: channel_intelligence
- Promotion: in recommendations
- Performance class: in slow_moving
- Price range: in slow_moving (revenue)
- Rating: in slow_moving
- Wastage range: in slow_moving

## 9. Quick Start for 4C

Minimal Python check (paste in a scratch script):

    import requests
    BASE = "http://localhost:5000/api/v1"

    r = requests.post(f"{BASE}/auth/login", json={
        "email": "admin@dineiq.local",
        "password": "Admin@12345"
    })
    token = r.json()["access_token"]
    H = {"Authorization": f"Bearer {token}"}

    print(requests.get(f"{BASE}/analytics/summary", headers=H).json())
    print(requests.get(f"{BASE}/analytics/recommendations", headers=H).json()[:2])

## 10. What is Ready vs Pending

### Ready now
- Auth + RBAC + JWT
- 21 tests passed
- All 4B outputs in DB (367 rows)
- All read endpoints
- Export CSV/XLSX (10 reports)
- Audit trail

### Pending from other students
- Spark predictions in dual_pipeline (Student 2)
- Menu performance classification full table (may need more columns)
- Customer segments table (currently only channel-level)
- Forecast actual vs predicted full time series

### What 4C can build immediately
1. Login page
2. Executive Dashboard (channel intelligence + recommendations)
3. Menu Dashboard (slow_moving + location_intelligence)
4. Dual-Pipeline Dashboard (dual_pipeline)
5. What-If viewer (what_if)
6. Export buttons (any report)

## 11. Contact

Backend owner: Student 4A
Questions about endpoint shape: see Section 5 above
