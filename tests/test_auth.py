import pytest

from app import create_app
from extensiones import db
from models import Usuario


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
def cliente(app):
    return app.test_client()


def registrar(cliente, email="ana@mail.com", password="clave123"):
    return cliente.post("/auth/registro", data={
        "nombre": "Ana",
        "email": email,
        "password": password,
        "confirmacion": password,
    })


def test_registro_guarda_password_hasheada(cliente):
    registrar(cliente)
    usuario = Usuario.query.filter_by(email="ana@mail.com").first()
    assert usuario is not None
    assert usuario.password_hash != "clave123"


def test_registro_rechaza_email_repetido(cliente):
    registrar(cliente)
    respuesta = registrar(cliente)
    assert "Ya existe una cuenta con ese email." in respuesta.get_data(as_text=True)
    assert Usuario.query.count() == 1


def test_ruta_protegida_redirige_al_login(cliente):
    respuesta = cliente.get("/dashboard/")
    assert respuesta.status_code == 302
    assert "/auth/login" in respuesta.headers["Location"]


def test_login_y_logout(cliente):
    registrar(cliente)
    respuesta = cliente.post("/auth/login", data={"email": "ana@mail.com", "password": "clave123"})
    assert respuesta.status_code == 302
    assert cliente.get("/dashboard/").status_code == 200

    cliente.get("/auth/logout")
    assert cliente.get("/dashboard/").status_code == 302


def test_login_con_password_incorrecta(cliente):
    registrar(cliente)
    respuesta = cliente.post("/auth/login", data={"email": "ana@mail.com", "password": "otra"})
    assert "Email o contraseña incorrectos." in respuesta.get_data(as_text=True)
