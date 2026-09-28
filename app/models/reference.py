from datetime import datetime
from ..extensions import db

class Restaurant(db.Model):
    __tablename__ = "restaurants"
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(120), nullable=False)
    city = db.Column(db.String(80))
    is_active = db.Column(db.Boolean, default=True)

class MenuCategory(db.Model):
    __tablename__ = "menu_categories"
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(120), nullable=False)

class MenuItem(db.Model):
    __tablename__ = "menu_items"
    id = db.Column(db.Integer, primary_key=True)
    sku = db.Column(db.String(40), unique=True, nullable=False)
    name = db.Column(db.String(150), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey("menu_categories.id"))
    base_price = db.Column(db.Numeric(10, 2))
    base_cost = db.Column(db.Numeric(10, 2))
    is_available = db.Column(db.Boolean, default=True)

class PricingHistory(db.Model):
    __tablename__ = "pricing_history"
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey("menu_items.id"), nullable=False)
    old_price = db.Column(db.Numeric(10, 2))
    new_price = db.Column(db.Numeric(10, 2), nullable=False)
    changed_at = db.Column(db.DateTime, nullable=False)

class Customer(db.Model):
    __tablename__ = "customers"
    id = db.Column(db.Integer, primary_key=True)
    external_id = db.Column(db.String(40), unique=True, nullable=False)
    segment = db.Column(db.String(40))

class Order(db.Model):
    __tablename__ = "orders"
    id = db.Column(db.Integer, primary_key=True)
    external_id = db.Column(db.String(40), unique=True, nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey("customers.id"))
    restaurant_id = db.Column(db.Integer, db.ForeignKey("restaurants.id"))
    channel = db.Column(db.String(30))
    status = db.Column(db.String(20))
    total_amount = db.Column(db.Numeric(12, 2))
    placed_at = db.Column(db.DateTime, nullable=False, index=True)

class OrderItem(db.Model):
    __tablename__ = "order_items"
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id", ondelete="CASCADE"))
    item_id = db.Column(db.Integer, db.ForeignKey("menu_items.id"))
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Numeric(10, 2))
    line_total = db.Column(db.Numeric(12, 2))

class Promotion(db.Model):
    __tablename__ = "promotions"
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(30), unique=True, nullable=False)
    name = db.Column(db.String(120))
    discount_pct = db.Column(db.Numeric(5, 2))
    starts_at = db.Column(db.DateTime)
    ends_at = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)

class Rating(db.Model):
    __tablename__ = "ratings"
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey("menu_items.id"))
    restaurant_id = db.Column(db.Integer, db.ForeignKey("restaurants.id"))
    customer_id = db.Column(db.Integer, db.ForeignKey("customers.id"))
    score = db.Column(db.SmallInteger)
    created_at = db.Column(db.DateTime, nullable=False)

class Inventory(db.Model):
    __tablename__ = "inventory"
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey("menu_items.id"))
    restaurant_id = db.Column(db.Integer, db.ForeignKey("restaurants.id"))
    stock_qty = db.Column(db.Numeric(12, 2))
    reorder_lvl = db.Column(db.Numeric(12, 2))
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)

class Wastage(db.Model):
    __tablename__ = "wastage"
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey("menu_items.id"))
    restaurant_id = db.Column(db.Integer, db.ForeignKey("restaurants.id"))
    quantity = db.Column(db.Numeric(12, 2))
    cost = db.Column(db.Numeric(12, 2))
    reason = db.Column(db.String(120))
    wasted_at = db.Column(db.DateTime, nullable=False)
