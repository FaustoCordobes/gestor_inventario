import re

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models import SUPPLIER_TYPES, Supplier

supplier_bp = Blueprint("supplier", __name__, url_prefix="/supplier")

EMAIL_PATTERN = re.compile(r"[^@\s]+@[^@\s]+\.[^@\s]+")
PHONE_PATTERN = re.compile(r"[0-9+\-().\s]+")

# Largo máximo de cada campo (el mismo que tiene la columna en la base de datos).
MAX_LENGTHS = {
    "name": ("El nombre", 100),
    "contact_name": ("La persona de contacto", 100),
    "phone": ("El teléfono", 30),
    "email": ("El email", 120),
    "address": ("La dirección", 150),
}


@supplier_bp.app_context_processor
def inject_supplier_types():
    return {"supplier_types": SUPPLIER_TYPES}


def _read_form():
    return {
        "supplier_type": request.form.get("supplier_type", "").strip(),
        "name": request.form.get("name", "").strip(),
        "contact_name": request.form.get("contact_name", "").strip(),
        "phone": request.form.get("phone", "").strip(),
        "email": request.form.get("email", "").strip(),
        "address": request.form.get("address", "").strip(),
        "description": request.form.get("description", "").strip(),
        "is_active": request.form.get("is_active") == "on",
    }


def _empty_form_data():
    return {
        "supplier_type": "", "name": "", "contact_name": "", "phone": "",
        "email": "", "address": "", "description": "", "is_active": True,
    }


def _supplier_form_data(supplier):
    return {
        "supplier_type": supplier.supplier_type,
        "name": supplier.name,
        "contact_name": supplier.contact_name or "",
        "phone": supplier.phone or "",
        "email": supplier.email or "",
        "address": supplier.address or "",
        "description": supplier.description or "",
        "is_active": bool(supplier.is_active),
    }


def _name_taken(column, value, supplier_id=None):
    query = Supplier.query.filter(func.lower(column) == value.lower())
    if supplier_id:
        query = query.filter(Supplier.id != supplier_id)
    return query.first() is not None


def _validate_supplier(data, supplier_id=None):
    """Devuelve un diccionario campo -> mensaje (si un campo tiene varios problemas, el primero)."""
    errors = {}

    def add_error(field, message):
        errors.setdefault(field, message)

    if data["supplier_type"] not in SUPPLIER_TYPES:
        add_error("supplier_type", "Elegí un tipo de proveedor válido.")
    if not data["name"]:
        add_error("name", "El nombre es obligatorio.")
    elif _name_taken(Supplier.name, data["name"], supplier_id):
        add_error("name", "Ya existe un proveedor con ese nombre.")
    if data["email"] and not EMAIL_PATTERN.fullmatch(data["email"]):
        add_error("email", "El email no es válido.")
    if data["phone"]:
        digits = sum(ch.isdigit() for ch in data["phone"])
        if not PHONE_PATTERN.fullmatch(data["phone"]) or digits < 6:
            add_error("phone", "El teléfono solo puede tener números, espacios, +, -, ( ) y punto (mínimo 6 dígitos).")

    for field, (label, maximum) in MAX_LENGTHS.items():
        if len(data[field]) > maximum:
            add_error(field, f"{label} puede tener hasta {maximum} caracteres.")

    return errors


def _save(supplier, data):
    supplier.supplier_type = data["supplier_type"]
    supplier.name = data["name"]
    supplier.contact_name = data["contact_name"] or None
    supplier.phone = data["phone"] or None
    supplier.email = data["email"] or None
    supplier.address = data["address"] or None
    supplier.description = data["description"] or None
    supplier.is_active = data["is_active"]
    try:
        db.session.add(supplier)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        flash("Ya existe un proveedor con ese nombre.", "error")
        return False
    except Exception:
        db.session.rollback()
        flash("No se pudo guardar el proveedor. Probá de nuevo.", "error")
        return False
    return True


@supplier_bp.route("/")
@login_required
def index():
    q = request.args.get("q", "").strip()

    query = Supplier.query
    if q:
        query = query.filter(Supplier.name.icontains(q, autoescape=True))

    suppliers = query.order_by(Supplier.name).all()
    return render_template("supplier/list.html", suppliers=suppliers, q=q)


@supplier_bp.route("/new", methods=["GET", "POST"])
@login_required
def new():
    if request.method == "POST":
        data = _read_form()
        errors = _validate_supplier(data)
        if errors:
            return render_template("supplier/create.html", supplier=None, data=data, errors=errors)

        if _save(Supplier(), data):
            flash("Proveedor creado.", "exito")
            return redirect(url_for("supplier.index"))
        return render_template("supplier/create.html", supplier=None, data=data, errors={})

    return render_template("supplier/create.html", supplier=None, data=_empty_form_data(), errors={})


@supplier_bp.route("/<int:supplier_id>")
@login_required
def detail(supplier_id):
    supplier = db.get_or_404(Supplier, supplier_id)
    return render_template("supplier/detail.html", supplier=supplier)


@supplier_bp.route("/<int:supplier_id>/edit", methods=["GET", "POST"])
@login_required
def edit(supplier_id):
    supplier = db.get_or_404(Supplier, supplier_id)

    if request.method == "POST":
        data = _read_form()
        errors = _validate_supplier(data, supplier_id=supplier.id)
        if errors:
            return render_template("supplier/create.html", supplier=supplier, data=data, errors=errors)

        if _save(supplier, data):
            flash("Proveedor actualizado.", "exito")
            return redirect(url_for("supplier.detail", supplier_id=supplier.id))
        return render_template("supplier/create.html", supplier=supplier, data=data, errors={})

    return render_template(
        "supplier/create.html", supplier=supplier, data=_supplier_form_data(supplier), errors={}
    )


@supplier_bp.route("/<int:supplier_id>/delete", methods=["GET", "POST"])
@login_required
def delete(supplier_id):
    supplier = db.get_or_404(Supplier, supplier_id)

    if request.method == "POST":
        try:
            db.session.delete(supplier)
            db.session.commit()
        except Exception:
            db.session.rollback()
            flash("No se pudo eliminar el proveedor. Probá de nuevo.", "error")
            return redirect(url_for("supplier.detail", supplier_id=supplier.id))
        flash(f"Proveedor «{supplier.name}» eliminado.", "exito")
        return redirect(url_for("supplier.index"))

    return render_template("supplier/confirm_delete.html", supplier=supplier)
