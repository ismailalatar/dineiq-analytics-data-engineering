import uuid
from flask import g

def init_audit_middleware(app):
    @app.before_request
    def _rid():
        g.request_id = str(uuid.uuid4())

    @app.after_request
    def _attach(response):
        if hasattr(g, "request_id"):
            response.headers["X-Request-Id"] = g.request_id
        return response
