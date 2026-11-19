from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from extensions import bcrypt, db, login_manager
from models import User

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirmation = request.form.get("confirmation", "")

        if not name or not email or not password:
            flash("Completá todos los campos.", "error")
        elif len(password) < 6:
            flash("La contraseña tiene que tener al menos 6 caracteres.", "error")
        elif password != confirmation:
            flash("Las contraseñas no coinciden.", "error")
        elif User.query.filter_by(email=email).first():
            flash("Ya existe una cuenta con ese email.", "error")
        else:
            password_hash = bcrypt.generate_password_hash(password).decode("utf-8")
            user = User(name=name, email=email, password_hash=password_hash)
            try:
                db.session.add(user)
                db.session.commit()
            except Exception:
                db.session.rollback()
                flash("No se pudo crear la cuenta. Probá de nuevo.", "error")
            else:
                flash("Cuenta creada. Ya podés iniciar sesión.", "exito")
                return redirect(url_for("auth.login"))

        return render_template("auth/register.html", name=name, email=email)

    return render_template("auth/register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = User.query.filter_by(email=email).first()

        if user and bcrypt.check_password_hash(user.password_hash, password):
            login_user(user)
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
