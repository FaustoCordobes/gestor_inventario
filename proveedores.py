from flask import Blueprint, render_template
from flask_login import login_required

proveedores_bp = Blueprint("proveedores", __name__, url_prefix="/proveedores")


@proveedores_bp.route("/")
@login_required
def lista():
    return render_template("en_construccion.html", titulo="Proveedores")
