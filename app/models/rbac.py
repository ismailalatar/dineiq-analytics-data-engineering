from datetime import datetime
from ..extensions import db, bcrypt

user_roles = db.Table(
    "user_roles",
    db.Column("user_id", db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    db.Column("role_id", db.Integer, db.ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
)

role_permissions = db.Table(
    "role_permissions",
    db.Column("role_id", db.Integer, db.ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
    db.Column("permission_id", db.Integer, db.ForeignKey("permissions.id", ondelete="CASCADE"), primary_key=True),
)

class Role(db.Model):
    __tablename__ = "roles"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.Text)
    users = db.relationship("User", secondary=user_roles, back_populates="roles")
    permissions = db.relationship("Permission", secondary=role_permissions, back_populates="roles")

class Permission(db.Model):
    __tablename__ = "permissions"
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(80), unique=True, nullable=False)
    description = db.Column(db.Text)
    roles = db.relationship("Role", secondary=role_permissions, back_populates="permissions")

class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(150))
    is_active = db.Column(db.Boolean, default=True)
    is_locked = db.Column(db.Boolean, default=False)
    failed_attempts = db.Column(db.Integer, default=0)
    last_login_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    roles = db.relationship("Role", secondary=user_roles, back_populates="users")

    def set_password(self, raw):
        self.password_hash = bcrypt.generate_password_hash(raw).decode("utf-8")

    def check_password(self, raw):
        return bcrypt.check_password_hash(self.password_hash, raw)

    def has_permission(self, code):
        return any(p.code == code for r in self.roles for p in r.permissions)

    def permissions_list(self):
        return sorted({p.code for r in self.roles for p in r.permissions})

    def to_dict(self):
        return {
            "id": self.id, "email": self.email, "username": self.username,
            "full_name": self.full_name, "is_active": self.is_active,
            "roles": [r.name for r in self.roles],
            "permissions": self.permissions_list(),
            "last_login_at": self.last_login_at.isoformat() if self.last_login_at else None,
        }
