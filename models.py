from datetime import datetime

from flask_login import UserMixin

from extensiones import db


class Usuario(UserMixin, db.Model):
    __tablename__ = "usuarios"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)


class Categoria(db.Model):
    __tablename__ = "categorias"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(60), unique=True, nullable=False)
    productos = db.relationship("Producto", back_populates="categoria")


class Proveedor(db.Model):
    __tablename__ = "proveedores"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), unique=True, nullable=False)
    contacto = db.Column(db.String(80))
    telefono = db.Column(db.String(30))
    email = db.Column(db.String(120))
    direccion = db.Column(db.String(150))
    activo = db.Column(db.Boolean, default=True)
    productos = db.relationship("Producto", back_populates="proveedor")


class Producto(db.Model):
    __tablename__ = "productos"

    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(20), unique=True, nullable=False)
    nombre = db.Column(db.String(100), unique=True, nullable=False)
    descripcion = db.Column(db.Text)
    precio = db.Column(db.Float, nullable=False)
    costo = db.Column(db.Float, nullable=False, default=0)
    stock = db.Column(db.Integer, nullable=False, default=0)
    stock_minimo = db.Column(db.Integer, nullable=False, default=5)
    fecha_alta = db.Column(db.DateTime, default=datetime.utcnow)
    categoria_id = db.Column(db.Integer, db.ForeignKey("categorias.id"), nullable=False)
    proveedor_id = db.Column(db.Integer, db.ForeignKey("proveedores.id"))
    categoria = db.relationship("Categoria", back_populates="productos")
    proveedor = db.relationship("Proveedor", back_populates="productos")

    def valor_stock(self):
        return self.precio * self.stock

    def margen(self):
        if self.precio == 0:
            return 0
        return round((self.precio - self.costo) / self.precio * 100, 1)

    def stock_bajo(self):
        return self.stock <= self.stock_minimo
