from flask import Blueprint, request, jsonify
from ..extensions import db
from ..core.rbac import require_permission
from ..models.reference import Restaurant, MenuItem

admin_bp = Blueprint("admin", __name__)

@admin_bp.route("/locations", methods=["GET"])
@require_permission("locations:read")
def list_locations():
    return jsonify([{"id": r.id, "code": r.code, "name": r.name, "city": r.city}
                    for r in Restaurant.query.all()])

@admin_bp.route("/locations", methods=["POST"])
@require_permission("locations:write")
def create_location():
    d = request.get_json() or {}
    r = Restaurant(code=d["code"], name=d["name"], city=d.get("city"))
    db.session.add(r); db.session.commit()
    return jsonify({"id": r.id}), 201

@admin_bp.route("/menu_items", methods=["GET"])
@require_permission("menu:read")
def list_menu():
    return jsonify([{"id": m.id, "sku": m.sku, "name": m.name,
                     "price": float(m.base_price or 0), "cost": float(m.base_cost or 0)}
                    for m in MenuItem.query.all()])

@admin_bp.route("/users", methods=["GET"])
@require_permission("users:read")
def list_users():
    from ..models.rbac import User
    return jsonify([u.to_dict() for u in User.query.all()])
