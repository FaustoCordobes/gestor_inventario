import pytest

from app import create_app
from extensions import db
from models import User


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


def register(client, email="ana@mail.com", password="clave123"):
    return client.post("/auth/register", data={
        "name": "Ana",
        "email": email,
        "password": password,
        "confirmation": password,
    })


def test_register_guarda_password_hasheada(client):
    register(client)
    user = User.query.filter_by(email="ana@mail.com").first()
    assert user is not None
    assert user.password_hash != "clave123"


def test_register_rechaza_email_repetido(client):
    register(client)
    response = register(client)
    assert "Ya existe una cuenta con ese email." in response.get_data(as_text=True)
    assert User.query.count() == 1


def test_ruta_protegida_redirige_al_login(client):
    response = client.get("/dashboard/")
    assert response.status_code == 302
    assert "/auth/login" in response.headers["Location"]


def test_login_y_logout(client):
    register(client)
    response = client.post("/auth/login", data={"email": "ana@mail.com", "password": "clave123"})
    assert response.status_code == 302
    assert client.get("/dashboard/").status_code == 200

    client.get("/auth/logout")
    assert client.get("/dashboard/").status_code == 302


def test_login_con_password_incorrecta(client):
    register(client)
    response = client.post("/auth/login", data={"email": "ana@mail.com", "password": "otra"})
    assert "Email o contraseña incorrectos." in response.get_data(as_text=True)
