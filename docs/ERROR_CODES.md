# Error Codes

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
