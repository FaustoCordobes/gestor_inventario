import pytest

from app import create_app
from app.extensions import db, oauth
from app.models import User


@pytest.fixture
def app():
    app = create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
    })
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


def simular_google(monkeypatch, userinfo):
    """Reemplaza la respuesta de Google para no depender de internet."""
    monkeypatch.setattr(
        oauth.google, "authorize_access_token", lambda: {"userinfo": userinfo}
    )


def test_callback_crea_usuario_nuevo_y_entra(client, monkeypatch):
    simular_google(monkeypatch, {"email": "Nuevo@Mail.com", "email_verified": True, "name": "Nuevo"})

    response = client.get("/auth/google/callback")

    assert response.status_code == 302
    user = User.query.filter_by(email="nuevo@mail.com").first()
    assert user is not None
    assert user.password_hash is None
    assert client.get("/dashboard/").status_code == 200


def test_callback_rechaza_email_no_verificado(client, monkeypatch):
    simular_google(monkeypatch, {"email": "x@mail.com", "email_verified": False, "name": "X"})

    client.get("/auth/google/callback")

    assert User.query.count() == 0
    assert client.get("/dashboard/").status_code == 302


def test_cuenta_de_google_no_entra_con_contrasena(client, monkeypatch):
    simular_google(monkeypatch, {"email": "g@mail.com", "email_verified": True, "name": "G"})
    client.get("/auth/google/callback")
    client.get("/auth/logout")

    response = client.post("/auth/login", data={"email": "g@mail.com", "password": "loquesea"})

    assert "Email o contraseña incorrectos." in response.get_data(as_text=True)


def test_sin_credenciales_el_boton_no_se_muestra_y_la_ruta_avisa(client):
    html = client.get("/auth/login").get_data(as_text=True)
    assert "Continuar con Google" not in html

    response = client.get("/auth/google", follow_redirects=True)
    assert "no está configurado" in response.get_data(as_text=True)
