from app import create_app
from app.extensions import db
from app.models.rbac import User, Role, Permission

PERMISSIONS = [
    "users:read","users:write","roles:read","roles:write",
    "locations:read","locations:write","menu:read","menu:write",
    "pricing:read","pricing:write","orders:read",
    "promotions:read","promotions:write","ratings:read",
    "inventory:read","inventory:write","wastage:read","wastage:write",
    "analytics:read","recommendations:read","recommendations:write",
    "audit:read","export:csv","export:xlsx","models:read","models:write",
]

ROLE_PERMS = {
    "restaurant_manager": [
        "roles:read","locations:read","menu:read","menu:write","pricing:read","pricing:write",
        "orders:read","promotions:read","promotions:write","ratings:read","inventory:read",
        "inventory:write","wastage:read","wastage:write","analytics:read",
        "recommendations:read","export:csv","export:xlsx","models:read",
    ],
    "analyst": [
        "roles:read","locations:read","menu:read","pricing:read","orders:read",
        "promotions:read","ratings:read","inventory:read","wastage:read","analytics:read",
        "recommendations:read","recommendations:write","export:csv","export:xlsx",
        "models:read","models:write",
    ],
    "regional_manager": [
        "roles:read","locations:read","menu:read","pricing:read","orders:read",
        "promotions:read","ratings:read","inventory:read","wastage:read","analytics:read",
        "recommendations:read","audit:read","export:csv","export:xlsx","models:read",
    ],
    "administrator": PERMISSIONS,
}

def seed():
    app = create_app()
    with app.app_context():
        db.create_all()
        pmap = {}
        for code in PERMISSIONS:
            p = Permission.query.filter_by(code=code).first() or Permission(code=code)
            if not p.id: db.session.add(p)
            pmap[code] = p
        db.session.commit()
        rmap = {}
        for rn, codes in ROLE_PERMS.items():
            r = Role.query.filter_by(name=rn).first() or Role(name=rn)
            if not r.id: db.session.add(r)
            r.permissions = [pmap[c] for c in codes]
            rmap[rn] = r
        db.session.commit()
        if not User.query.filter_by(email="admin@dineiq.local").first():
            u = User(email="admin@dineiq.local", username="admin", full_name="System Admin")
            u.set_password("Admin@12345")
            u.roles = [rmap["administrator"]]
            db.session.add(u); db.session.commit()
            print("Admin: admin@dineiq.local / Admin@12345")
        print("Seed OK.")

if __name__ == "__main__":
    seed()
