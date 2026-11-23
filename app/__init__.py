from flask import Flask, redirect, render_template, url_for
from werkzeug.middleware.proxy_fix import ProxyFix

from app.blueprints.auth import auth_bp
from app.blueprints.dashboard import dashboard_bp
from app.blueprints.inventory import inventory_bp
from app.blueprints.supplier import supplier_bp
from app.config import Config
from app.extensions import bcrypt, db, login_manager, oauth


def create_app(config_extra=None):
    app = Flask(__name__)
    app.config.from_object(Config)
    if config_extra:
        app.config.update(config_extra)

    # Detrás del proxy de Render, para que los links externos salgan con https.
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    oauth.init_app(app)
    oauth.register(
        name="google",
        client_id=app.config.get("GOOGLE_CLIENT_ID"),
        client_secret=app.config.get("GOOGLE_CLIENT_SECRET"),
        server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
        client_kwargs={"scope": "openid email profile"},
    )

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
