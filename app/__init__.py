from flask import Flask, redirect, render_template, url_for

from app.blueprints.auth import auth_bp
from app.blueprints.dashboard import dashboard_bp
from app.blueprints.inventory import inventory_bp
from app.blueprints.supplier import supplier_bp
from app.config import Config
from app.extensions import bcrypt, db, login_manager


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
    app.register_blueprint(inventory_bp)
    app.register_blueprint(supplier_bp)

    @app.route("/")
    def home():
        return redirect(url_for("dashboard.index"))

    @app.errorhandler(404)
    def not_found(error):
        return render_template("404.html"), 404

    @app.errorhandler(500)
    def server_error(error):
        return render_template("500.html"), 500

    with app.app_context():
        db.create_all()

    return app
