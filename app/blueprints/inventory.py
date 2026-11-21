import math

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models import Category, Product, Supplier

inventory_bp = Blueprint("inventory", __name__, url_prefix="/inventory")


# ---------------------------------------------------------------------------
# Auxiliares
# ---------------------------------------------------------------------------

def _to_number(text, integer=False):
    """Convierte un texto a número. Devuelve None si no es un número válido."""
    text = (text or "").strip().replace(",", ".")
    try:
        value = int(text) if integer else float(text)
    except ValueError:
        return None
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value


def _read_form():
    """Devuelve los textos tal como los escribió la persona (para volver a mostrarlos)."""
    return {
        "code": request.form.get("code", "").strip(),
        "name": request.form.get("name", "").strip(),
        "description": request.form.get("description", "").strip(),
        "price": request.form.get("price", "").strip(),
        "cost": request.form.get("cost", "").strip(),
        "stock": request.form.get("stock", "").strip(),
        "min_stock": request.form.get("min_stock", "").strip(),
        "category_id": request.form.get("category_id", "").strip(),
        "supplier_id": request.form.get("supplier_id", "").strip(),
    }


def _validate_product(data, product_id=None):
    """Valida los datos del formulario.

    Devuelve (errores, limpios): una lista de mensajes y un diccionario con
    los valores ya convertidos a su tipo final.
    """
    errors = []
    clean = {}

    # Campos vacíos
    required_fields = {
        "code": "El código",
        "name": "El nombre",
        "price": "El precio",
        "stock": "El stock",
        "category_id": "La categoría",
    }
    for field, label in required_fields.items():
        if not data[field]:
            errors.append(f"{label} es obligatorio.")

    if len(data["code"]) > 20:
        errors.append("El código puede tener hasta 20 caracteres.")
    if len(data["name"]) > 100:
        errors.append("El nombre puede tener hasta 100 caracteres.")

    # Números: tienen que ser números y no pueden ser negativos
    numeric_fields = [
        ("price", "El precio", False, True),
        ("cost", "El costo", False, False),
        ("stock", "El stock", True, True),
        ("min_stock", "El stock mínimo", True, False),
    ]
    defaults = {"cost": 0.0, "min_stock": 5}
    for field, label, integer, required in numeric_fields:
        text = data[field]
        if not text:
            if not required:
                clean[field] = defaults[field]
            continue
        value = _to_number(text, integer=integer)
        if value is None:
            kind = "un número entero" if integer else "un número"
            errors.append(f"{label} tiene que ser {kind}.")
        elif value < 0:
            errors.append(f"{label} no puede ser negativo.")
        else:
            clean[field] = value

    # Categoría y proveedor tienen que existir
    category = None
    if data["category_id"]:
        if data["category_id"].isdigit():
            category = db.session.get(Category, int(data["category_id"]))
        if category is None:
            errors.append("Elegí una categoría de la lista.")
    clean["category_id"] = category.id if category else None

    supplier_id = None
    if data["supplier_id"]:
        supplier = None
        if data["supplier_id"].isdigit():
            supplier = db.session.get(Supplier, int(data["supplier_id"]))
        if supplier is None:
            errors.append("Elegí un proveedor de la lista.")
        else:
            supplier_id = supplier.id
    clean["supplier_id"] = supplier_id

    # Duplicados (sin distinguir mayúsculas; al editar se ignora el propio producto)
    if data["code"]:
        query = Product.query.filter(func.lower(Product.code) == data["code"].lower())
        if product_id:
            query = query.filter(Product.id != product_id)
        if query.first():
            errors.append("Ya existe un producto con ese código.")
    if data["name"]:
        query = Product.query.filter(func.lower(Product.name) == data["name"].lower())
        if product_id:
            query = query.filter(Product.id != product_id)
        if query.first():
            errors.append("Ya existe un producto con ese nombre.")

    clean["code"] = data["code"]
    clean["name"] = data["name"]
    clean["description"] = data["description"] or None
    return errors, clean


def _product_form_data(product):
    """Pasa un producto existente al formato de texto que usa el formulario."""
    return {
        "code": product.code,
        "name": product.name,
        "description": product.description or "",
        "price": f"{product.price:g}",
        "cost": f"{product.cost:g}",
        "stock": str(product.stock),
        "min_stock": str(product.min_stock),
        "category_id": str(product.category_id),
        "supplier_id": str(product.supplier_id or ""),
    }


def _empty_form_data():
    return {
        "code": "", "name": "", "description": "", "price": "", "cost": "",
        "stock": "", "min_stock": "5", "category_id": "", "supplier_id": "",
    }


def _render_form(product, data):
    return render_template(
        "inventory/form.html",
        product=product,
        data=data,
        categories=Category.query.order_by(Category.name).all(),
        suppliers=Supplier.query.filter_by(is_active=True).order_by(Supplier.name).all(),
    )


def _save(product, clean):
    """Copia los datos limpios al producto y lo guarda. Devuelve True si salió bien."""
    for field, value in clean.items():
        setattr(product, field, value)
    try:
        db.session.add(product)
        db.session.commit()
    except IntegrityError:
        # Otra persona pudo haber creado el mismo código justo antes que vos.
        db.session.rollback()
        flash("Ya existe un producto con ese código o nombre.", "error")
    except Exception:
        db.session.rollback()
        flash("No se pudo guardar el producto. Probá de nuevo.", "error")
    else:
        return True
    return False


# ---------------------------------------------------------------------------
# Productos
# ---------------------------------------------------------------------------

@inventory_bp.route("/")
@login_required
def index():
    q = request.args.get("q", "").strip()
    category_id = request.args.get("category", type=int)

    query = Product.query
    if q:
        pattern = q.lower()
        query = query.filter(
            db.or_(
                func.lower(Product.name).contains(pattern, autoescape=True),
                func.lower(Product.code).contains(pattern, autoescape=True),
            )
        )
    if category_id:
        query = query.filter(Product.category_id == category_id)

    products = query.order_by(Product.name).all()
    return render_template(
        "inventory/list.html",
        products=products,
        categories=Category.query.order_by(Category.name).all(),
        q=q,
        category_id=category_id,
    )


@inventory_bp.route("/new", methods=["GET", "POST"])
@login_required
def new():
    if request.method == "POST":
        data = _read_form()
        errors, clean = _validate_product(data)
        if errors:
            for error in errors:
                flash(error, "error")
            return _render_form(None, data)

        if _save(Product(), clean):
            flash("Producto creado.", "exito")
            return redirect(url_for("inventory.index"))
        return _render_form(None, data)

    return _render_form(None, _empty_form_data())


@inventory_bp.route("/<int:product_id>/edit", methods=["GET", "POST"])
@login_required
def edit(product_id):
    product = db.get_or_404(Product, product_id)

    if request.method == "POST":
        data = _read_form()
        errors, clean = _validate_product(data, product_id=product.id)
        if errors:
            for error in errors:
                flash(error, "error")
            return _render_form(product, data)

        if _save(product, clean):
            flash("Producto actualizado.", "exito")
            return redirect(url_for("inventory.index"))
        return _render_form(product, data)

    return _render_form(product, _product_form_data(product))


@inventory_bp.route("/<int:product_id>/delete", methods=["GET", "POST"])
@login_required
def delete(product_id):
    """GET muestra la pantalla de confirmación; POST borra el producto."""
    product = db.get_or_404(Product, product_id)

    if request.method == "POST":
        try:
            db.session.delete(product)
            db.session.commit()
        except Exception:
            db.session.rollback()
            flash("No se pudo eliminar el producto. Probá de nuevo.", "error")
            return redirect(url_for("inventory.index"))
        flash(f"Producto «{product.name}» eliminado.", "exito")
        return redirect(url_for("inventory.index"))

    return render_template("inventory/confirm_delete.html", product=product)


# ---------------------------------------------------------------------------
# Categorías
# ---------------------------------------------------------------------------

@inventory_bp.route("/categories", methods=["GET", "POST"])
@login_required
def categories():
    name = ""
    if request.method == "POST":
        name = request.form.get("name", "").strip()

        if not name:
            flash("El nombre de la categoría es obligatorio.", "error")
        elif len(name) > 60:
            flash("El nombre puede tener hasta 60 caracteres.", "error")
        elif Category.query.filter(func.lower(Category.name) == name.lower()).first():
            flash("Ya existe una categoría con ese nombre.", "error")
        else:
            try:
                db.session.add(Category(name=name))
                db.session.commit()
            except IntegrityError:
                db.session.rollback()
                flash("Ya existe una categoría con ese nombre.", "error")
            except Exception:
                db.session.rollback()
                flash("No se pudo crear la categoría. Probá de nuevo.", "error")
            else:
                flash("Categoría creada.", "exito")
                return redirect(url_for("inventory.categories"))

    q = request.args.get("q", "").strip()
    query = Category.query
    if q:
        query = query.filter(Category.name.icontains(q, autoescape=True))
    all_categories = query.order_by(Category.name).all()
    return render_template("inventory/categories.html", categories=all_categories, name=name, q=q)


@inventory_bp.route("/categories/<int:category_id>/delete", methods=["POST"])
@login_required
def delete_category(category_id):
    category = db.get_or_404(Category, category_id)

    if category.products:
        flash(
            f"No se puede eliminar «{category.name}» porque tiene "
            f"{len(category.products)} producto(s). Movelos a otra categoría primero.",
            "error",
        )
        return redirect(url_for("inventory.categories"))

    try:
        db.session.delete(category)
        db.session.commit()
    except Exception:
        db.session.rollback()
        flash("No se pudo eliminar la categoría. Probá de nuevo.", "error")
    else:
        flash("Categoría eliminada.", "exito")
    return redirect(url_for("inventory.categories"))
