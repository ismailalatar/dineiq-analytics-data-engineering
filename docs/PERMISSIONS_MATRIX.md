# Permissions Matrix

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
