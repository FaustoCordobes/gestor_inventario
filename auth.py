from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from extensiones import bcrypt, db, login_manager
from models import Usuario

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@login_manager.user_loader
def cargar_usuario(usuario_id):
    return db.session.get(Usuario, int(usuario_id))


@auth_bp.route("/registro", methods=["GET", "POST"])
def registro():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))

    if request.method == "POST":
        nombre = request.form.get("nombre", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirmacion = request.form.get("confirmacion", "")

        if not nombre or not email or not password:
            flash("Completá todos los campos.", "error")
        elif len(password) < 6:
            flash("La contraseña tiene que tener al menos 6 caracteres.", "error")
        elif password != confirmacion:
            flash("Las contraseñas no coinciden.", "error")
        elif Usuario.query.filter_by(email=email).first():
            flash("Ya existe una cuenta con ese email.", "error")
        else:
            password_hash = bcrypt.generate_password_hash(password).decode("utf-8")
            usuario = Usuario(nombre=nombre, email=email, password_hash=password_hash)
            try:
                db.session.add(usuario)
                db.session.commit()
            except Exception:
                db.session.rollback()
                flash("No se pudo crear la cuenta. Probá de nuevo.", "error")
            else:
                flash("Cuenta creada. Ya podés iniciar sesión.", "exito")
                return redirect(url_for("auth.login"))

        return render_template("auth/registro.html", nombre=nombre, email=email)

    return render_template("auth/registro.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        usuario = Usuario.query.filter_by(email=email).first()

        if usuario and bcrypt.check_password_hash(usuario.password_hash, password):
            login_user(usuario)
            return redirect(url_for("dashboard.index"))

        flash("Email o contraseña incorrectos.", "error")
        return render_template("auth/login.html", email=email)

    return render_template("auth/login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Cerraste sesión.", "exito")
    return redirect(url_for("auth.login"))
