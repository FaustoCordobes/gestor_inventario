from flask import Flask, redirect, render_template, url_for

from auth import auth_bp
from config import Config
from dashboard import dashboard_bp
from extensiones import bcrypt, db, login_manager
from inventario import inventario_bp
from proveedores import proveedores_bp


def create_app(config_extra=None):
    app = Flask(__name__)
    app.config.from_object(Config)
    if config_extra:
        app.config.update(config_extra)

    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(inventario_bp)
    app.register_blueprint(proveedores_bp)

    @app.route("/")
    def inicio():
        return redirect(url_for("dashboard.index"))

    @app.errorhandler(404)
    def no_encontrado(error):
        return render_template("404.html"), 404

    @app.errorhandler(500)
    def error_servidor(error):
        return render_template("500.html"), 500

    with app.app_context():
        db.create_all()

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
