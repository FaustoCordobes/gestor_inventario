import math

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError

from extensiones import db
from models import Categoria, Producto, Proveedor

inventario_bp = Blueprint("inventario", __name__, url_prefix="/inventario")


# ---------------------------------------------------------------------------
# Auxiliares
# ---------------------------------------------------------------------------

def _a_numero(texto, entero=False):
    """Convierte un texto a número. Devuelve None si no es un número válido."""
    texto = (texto or "").strip().replace(",", ".")
    try:
        valor = int(texto) if entero else float(texto)
    except ValueError:
        return None
    if isinstance(valor, float) and not math.isfinite(valor):
        return None
    return valor


def _leer_formulario():
    """Devuelve los textos tal como los escribió la persona (para volver a mostrarlos)."""
    return {
        "codigo": request.form.get("codigo", "").strip(),
        "nombre": request.form.get("nombre", "").strip(),
        "descripcion": request.form.get("descripcion", "").strip(),
        "precio": request.form.get("precio", "").strip(),
        "costo": request.form.get("costo", "").strip(),
        "stock": request.form.get("stock", "").strip(),
        "stock_minimo": request.form.get("stock_minimo", "").strip(),
        "categoria_id": request.form.get("categoria_id", "").strip(),
        "proveedor_id": request.form.get("proveedor_id", "").strip(),
    }


def _validar_producto(datos, producto_id=None):
    """Valida los datos del formulario.

    Devuelve (errores, limpios): una lista de mensajes y un diccionario con
    los valores ya convertidos a su tipo final.
    """
    errores = []
    limpios = {}

    # Campos vacíos
    obligatorios = {
        "codigo": "El código",
        "nombre": "El nombre",
        "precio": "El precio",
        "stock": "El stock",
        "categoria_id": "La categoría",
    }
    for campo, etiqueta in obligatorios.items():
        if not datos[campo]:
            errores.append(f"{etiqueta} es obligatorio.")

    if len(datos["codigo"]) > 20:
        errores.append("El código puede tener hasta 20 caracteres.")
    if len(datos["nombre"]) > 100:
        errores.append("El nombre puede tener hasta 100 caracteres.")

    # Números: tienen que ser números y no pueden ser negativos
    campos_numericos = [
        ("precio", "El precio", False, True),
        ("costo", "El costo", False, False),
        ("stock", "El stock", True, True),
        ("stock_minimo", "El stock mínimo", True, False),
    ]
    por_defecto = {"costo": 0.0, "stock_minimo": 5}
    for campo, etiqueta, entero, obligatorio in campos_numericos:
        texto = datos[campo]
        if not texto:
            if not obligatorio:
                limpios[campo] = por_defecto[campo]
            continue
        valor = _a_numero(texto, entero=entero)
        if valor is None:
            tipo = "un número entero" if entero else "un número"
            errores.append(f"{etiqueta} tiene que ser {tipo}.")
        elif valor < 0:
            errores.append(f"{etiqueta} no puede ser negativo.")
        else:
            limpios[campo] = valor

    # Categoría y proveedor tienen que existir
    categoria = None
    if datos["categoria_id"]:
        if datos["categoria_id"].isdigit():
            categoria = db.session.get(Categoria, int(datos["categoria_id"]))
        if categoria is None:
            errores.append("Elegí una categoría de la lista.")
    limpios["categoria_id"] = categoria.id if categoria else None

    proveedor_id = None
    if datos["proveedor_id"]:
        proveedor = None
        if datos["proveedor_id"].isdigit():
            proveedor = db.session.get(Proveedor, int(datos["proveedor_id"]))
        if proveedor is None:
            errores.append("Elegí un proveedor de la lista.")
        else:
            proveedor_id = proveedor.id
    limpios["proveedor_id"] = proveedor_id

    # Duplicados (sin distinguir mayúsculas; al editar se ignora el propio producto)
    if datos["codigo"]:
        consulta = Producto.query.filter(func.lower(Producto.codigo) == datos["codigo"].lower())
        if producto_id:
            consulta = consulta.filter(Producto.id != producto_id)
        if consulta.first():
            errores.append("Ya existe un producto con ese código.")
    if datos["nombre"]:
        consulta = Producto.query.filter(func.lower(Producto.nombre) == datos["nombre"].lower())
        if producto_id:
            consulta = consulta.filter(Producto.id != producto_id)
        if consulta.first():
            errores.append("Ya existe un producto con ese nombre.")

    limpios["codigo"] = datos["codigo"]
    limpios["nombre"] = datos["nombre"]
    limpios["descripcion"] = datos["descripcion"] or None
    return errores, limpios


def _datos_de_producto(producto):
    """Pasa un producto existente al formato de texto que usa el formulario."""
    return {
        "codigo": producto.codigo,
        "nombre": producto.nombre,
        "descripcion": producto.descripcion or "",
        "precio": f"{producto.precio:g}",
        "costo": f"{producto.costo:g}",
        "stock": str(producto.stock),
        "stock_minimo": str(producto.stock_minimo),
        "categoria_id": str(producto.categoria_id),
        "proveedor_id": str(producto.proveedor_id or ""),
    }


def _datos_vacios():
    return {
        "codigo": "", "nombre": "", "descripcion": "", "precio": "", "costo": "",
        "stock": "", "stock_minimo": "5", "categoria_id": "", "proveedor_id": "",
    }


def _render_formulario(producto, datos):
    return render_template(
        "inventario/form.html",
        producto=producto,
        datos=datos,
        categorias=Categoria.query.order_by(Categoria.nombre).all(),
        proveedores=Proveedor.query.filter_by(activo=True).order_by(Proveedor.nombre).all(),
    )


def _guardar(producto, limpios):
    """Copia los datos limpios al producto y lo guarda. Devuelve True si salió bien."""
    for campo, valor in limpios.items():
        setattr(producto, campo, valor)
    try:
        db.session.add(producto)
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

@inventario_bp.route("/")
@login_required
def lista():
    q = request.args.get("q", "").strip()
    categoria_id = request.args.get("categoria", type=int)

    consulta = Producto.query
    if q:
        patron = q.lower()
        consulta = consulta.filter(
            db.or_(
                func.lower(Producto.nombre).contains(patron, autoescape=True),
                func.lower(Producto.codigo).contains(patron, autoescape=True),
            )
        )
    if categoria_id:
        consulta = consulta.filter(Producto.categoria_id == categoria_id)

    productos = consulta.order_by(Producto.nombre).all()
    return render_template(
        "inventario/lista.html",
        productos=productos,
        categorias=Categoria.query.order_by(Categoria.nombre).all(),
        q=q,
        categoria_id=categoria_id,
    )


@inventario_bp.route("/nuevo", methods=["GET", "POST"])
@login_required
def nuevo():
    if request.method == "POST":
        datos = _leer_formulario()
        errores, limpios = _validar_producto(datos)
        if errores:
            for error in errores:
                flash(error, "error")
            return _render_formulario(None, datos)

        if _guardar(Producto(), limpios):
            flash("Producto creado.", "exito")
            return redirect(url_for("inventario.lista"))
        return _render_formulario(None, datos)

    return _render_formulario(None, _datos_vacios())


@inventario_bp.route("/<int:producto_id>/editar", methods=["GET", "POST"])
@login_required
def editar(producto_id):
    producto = db.get_or_404(Producto, producto_id)

    if request.method == "POST":
        datos = _leer_formulario()
        errores, limpios = _validar_producto(datos, producto_id=producto.id)
        if errores:
            for error in errores:
                flash(error, "error")
            return _render_formulario(producto, datos)

        if _guardar(producto, limpios):
            flash("Producto actualizado.", "exito")
            return redirect(url_for("inventario.lista"))
        return _render_formulario(producto, datos)

    return _render_formulario(producto, _datos_de_producto(producto))


@inventario_bp.route("/<int:producto_id>/eliminar", methods=["GET", "POST"])
@login_required
def eliminar(producto_id):
    """GET muestra la pantalla de confirmación; POST borra el producto."""
    producto = db.get_or_404(Producto, producto_id)

    if request.method == "POST":
        try:
            db.session.delete(producto)
            db.session.commit()
        except Exception:
            db.session.rollback()
            flash("No se pudo eliminar el producto. Probá de nuevo.", "error")
            return redirect(url_for("inventario.lista"))
        flash(f"Producto «{producto.nombre}» eliminado.", "exito")
        return redirect(url_for("inventario.lista"))

    return render_template("inventario/confirmar_eliminar.html", producto=producto)


# ---------------------------------------------------------------------------
# Categorías
# ---------------------------------------------------------------------------

@inventario_bp.route("/categorias", methods=["GET", "POST"])
@login_required
def categorias():
    nombre = ""
    if request.method == "POST":
        nombre = request.form.get("nombre", "").strip()

        if not nombre:
            flash("El nombre de la categoría es obligatorio.", "error")
        elif len(nombre) > 60:
            flash("El nombre puede tener hasta 60 caracteres.", "error")
        elif Categoria.query.filter(func.lower(Categoria.nombre) == nombre.lower()).first():
            flash("Ya existe una categoría con ese nombre.", "error")
        else:
            try:
                db.session.add(Categoria(nombre=nombre))
                db.session.commit()
            except IntegrityError:
                db.session.rollback()
                flash("Ya existe una categoría con ese nombre.", "error")
            except Exception:
                db.session.rollback()
                flash("No se pudo crear la categoría. Probá de nuevo.", "error")
            else:
                flash("Categoría creada.", "exito")
                return redirect(url_for("inventario.categorias"))

    todas = Categoria.query.order_by(Categoria.nombre).all()
    return render_template("inventario/categorias.html", categorias=todas, nombre=nombre)


@inventario_bp.route("/categorias/<int:categoria_id>/eliminar", methods=["POST"])
@login_required
def eliminar_categoria(categoria_id):
    categoria = db.get_or_404(Categoria, categoria_id)

    if categoria.productos:
        flash(
            f"No se puede eliminar «{categoria.nombre}» porque tiene "
            f"{len(categoria.productos)} producto(s). Movelos a otra categoría primero.",
            "error",
        )
        return redirect(url_for("inventario.categorias"))

    try:
        db.session.delete(categoria)
        db.session.commit()
    except Exception:
        db.session.rollback()
        flash("No se pudo eliminar la categoría. Probá de nuevo.", "error")
    else:
        flash("Categoría eliminada.", "exito")
    return redirect(url_for("inventario.categorias"))
