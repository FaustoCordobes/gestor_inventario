from datetime import datetime

from flask_login import UserMixin

from app.extensions import db


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    # Vacío para las cuentas creadas con Google (no tienen contraseña propia).
    password_hash = db.Column(db.String(128), nullable=True)


class Category(db.Model):
    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(60), unique=True, nullable=False)
    products = db.relationship("Product", back_populates="category")


SUPPLIER_TYPES = ("Distributor", "Manufacturer", "Importer", "Workshop", "Wholesaler", "Other")


class Supplier(db.Model):
    __tablename__ = "suppliers"

    id = db.Column(db.Integer, primary_key=True)
    supplier_type = db.Column(db.String(30), nullable=False)
    name = db.Column(db.String(100), unique=True, nullable=False)
    contact_name = db.Column(db.String(100), nullable=True)
    phone = db.Column(db.String(30))
    email = db.Column(db.String(120))
    description = db.Column(db.Text)
    address = db.Column(db.String(150), nullable=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    products = db.relationship("Product", back_populates="supplier")


class Product(db.Model):
    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    cost = db.Column(db.Float, nullable=False, default=0)
    stock = db.Column(db.Integer, nullable=False, default=0)
    min_stock = db.Column(db.Integer, nullable=False, default=5)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=False)
    supplier_id = db.Column(db.Integer, db.ForeignKey("suppliers.id"))
    category = db.relationship("Category", back_populates="products")
    supplier = db.relationship("Supplier", back_populates="products")

    def stock_value(self):
        return self.price * self.stock

    def margin(self):
        if self.price == 0:
            return 0
        return round((self.price - self.cost) / self.price * 100, 1)

    def is_low_stock(self):
        return self.stock <= self.min_stock
