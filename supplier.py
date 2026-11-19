import re

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError

from extensions import db
from models import Supplier

supplier_bp = Blueprint("supplier", __name__, url_prefix="/supplier")

EMAIL_PATTERN = re.compile(r"[^@\s]+@[^@\s]+\.[^@\s]+")


def _read_form():
    return {
        "type_supplier": request.form.get("type_supplier", "").strip(),
        "name": request.form.get("name", "").strip(),
        "last_name": request.form.get("last_name", "").strip(),
        "phone": request.form.get("phone", "").strip(),
        "email": request.form.get("email", "").strip(),
        "address": request.form.get("address", "").strip(),
        "description": request.form.get("description", "").strip(),
        "is_active": request.form.get("is_active") == "on",
    }


def _empty_form_data():
    return {
        "type_supplier": "", "name": "", "last_name": "", "phone": "",
        "email": "", "address": "", "description": "", "is_active": True,
    }


def _supplier_form_data(supplier):
    return {
        "type_supplier": supplier.type_supplier,
        "name": supplier.name,
        "last_name": supplier.last_name,
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
    errors = []

    if not data["type_supplier"]:
        errors.append("El tipo de proveedor es obligatorio.")
    if not data["name"]:
        errors.append("El nombre es obligatorio.")
    elif _name_taken(Supplier.name, data["name"], supplier_id):
        errors.append("Ya existe un proveedor con ese nombre.")
    if not data["last_name"]:
        errors.append("El apellido es obligatorio.")
    elif _name_taken(Supplier.last_name, data["last_name"], supplier_id):
        errors.append("Ya existe un proveedor con ese apellido.")
    if data["email"] and not EMAIL_PATTERN.fullmatch(data["email"]):
        errors.append("El email no es válido.")

    return errors


def _save(supplier, data):
    supplier.type_supplier = data["type_supplier"]
    supplier.name = data["name"]
    supplier.last_name = data["last_name"]
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
        flash("Ya existe un proveedor con ese nombre o apellido.", "error")
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
            for error in errors:
                flash(error, "error")
            return render_template("supplier/create.html", supplier=None, data=data)

        if _save(Supplier(), data):
            flash("Proveedor creado.", "exito")
            return redirect(url_for("supplier.index"))
        return render_template("supplier/create.html", supplier=None, data=data)

    return render_template("supplier/create.html", supplier=None, data=_empty_form_data())


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
            for error in errors:
                flash(error, "error")
            return render_template("supplier/create.html", supplier=supplier, data=data)

        if _save(supplier, data):
            flash("Proveedor actualizado.", "exito")
            return redirect(url_for("supplier.detail", supplier_id=supplier.id))
        return render_template("supplier/create.html", supplier=supplier, data=data)

    return render_template("supplier/create.html", supplier=supplier, data=_supplier_form_data(supplier))


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
        flash(f"Proveedor «{supplier.name} {supplier.last_name}» eliminado.", "exito")
        return redirect(url_for("supplier.index"))

    return render_template("supplier/confirm_delete.html", supplier=supplier)
