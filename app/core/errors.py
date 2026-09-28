from flask import jsonify
from werkzeug.exceptions import HTTPException

ERROR_CODES = {
    400: "VALIDATION_ERROR", 401: "AUTH_UNAUTHORIZED",
    403: "RBAC_PERMISSION_DENIED", 404: "RESOURCE_NOT_FOUND",
    409: "CONFLICT_DUPLICATE", 422: "UNPROCESSABLE_ENTITY",
    429: "RATE_LIMIT_EXCEEDED", 500: "INTERNAL_ERROR",
    503: "SERVICE_UNAVAILABLE",
}

class AppError(Exception):
    def __init__(self, code, message, status=400, details=None):
        self.code, self.message, self.status, self.details = code, message, status, details

def register_error_handlers(app):
    @app.errorhandler(AppError)
    def _app(e):
        return jsonify({"error": {"code": e.code, "message": e.message, "details": e.details}}), e.status

    @app.errorhandler(HTTPException)
    def _http(e):
        return jsonify({"error": {"code": ERROR_CODES.get(e.code, "HTTP_ERROR"), "message": e.description, "details": None}}), e.code

    @app.errorhandler(Exception)
    def _unexpected(e):
        app.logger.exception("Unhandled")
        return jsonify({"error": {"code": "INTERNAL_ERROR", "message": "Unexpected error.", "details": None}}), 500
