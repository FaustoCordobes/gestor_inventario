from flask import Blueprint, render_template
from flask_login import login_required

inventario_bp = Blueprint("inventario", __name__, url_prefix="/inventario")


@inventario_bp.route("/")
@login_required
def lista():
    return render_template("en_construccion.html", titulo="Inventario")


@inventario_bp.route("/nuevo", methods=["GET", "POST"])
@login_required
def nuevo():
    return render_template("en_construccion.html", titulo="Nuevo producto")


@inventario_bp.route("/categorias", methods=["GET", "POST"])
@login_required
def categorias():
    return render_template("en_construccion.html", titulo="Categorías")
