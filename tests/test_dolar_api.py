import pytest
import requests

from app import create_app
from app.extensions import db
from app.services import exchange_rate


class RespuestaFalsa:
    def __init__(self, status_code, datos=None):
        self.status_code = status_code
        self.datos = datos

    def json(self):
        if self.datos is None:
            raise ValueError("Sin JSON")
        return self.datos


COTIZACION = {"compra": 1000.0, "venta": 1050.0, "fechaActualizacion": "2026-11-23T15:00:00.000Z"}


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
    client = app.test_client()
    client.post("/auth/register", data={
        "name": "Ana",
        "email": "ana@mail.com",
        "password": "clave123",
        "confirmation": "clave123",
    })
    client.post("/auth/login", data={"email": "ana@mail.com", "password": "clave123"})
    return client


def test_cotizacion_correcta(monkeypatch):
    monkeypatch.setattr(exchange_rate.requests, "get", lambda *a, **k: RespuestaFalsa(200, COTIZACION))
    dolar = exchange_rate.get_dollar_rate()
    assert dolar["buy"] == 1000.0
    assert dolar["sell"] == 1050.0


def test_api_responde_error(monkeypatch):
    monkeypatch.setattr(exchange_rate.requests, "get", lambda *a, **k: RespuestaFalsa(404))
    assert exchange_rate.get_dollar_rate() is None


def test_sin_conexion(monkeypatch):
    def falla(*a, **k):
        raise requests.ConnectionError("sin internet")
    monkeypatch.setattr(exchange_rate.requests, "get", falla)
    assert exchange_rate.get_dollar_rate() is None


def test_dashboard_muestra_cotizacion(client, monkeypatch):
    monkeypatch.setattr(exchange_rate.requests, "get", lambda *a, **k: RespuestaFalsa(200, COTIZACION))
    html = client.get("/dashboard/").get_data(as_text=True)
    assert "Cotización del dólar oficial" in html
    assert "$1050.00" in html


def test_dashboard_funciona_sin_cotizacion(client, monkeypatch):
    def falla(*a, **k):
        raise requests.Timeout("tardó demasiado")
    monkeypatch.setattr(exchange_rate.requests, "get", falla)
    respuesta = client.get("/dashboard/")
    assert respuesta.status_code == 200
    assert "No se pudo obtener la cotización del dólar" in respuesta.get_data(as_text=True)


def test_ruta_json(client, monkeypatch):
    monkeypatch.setattr(exchange_rate.requests, "get", lambda *a, **k: RespuestaFalsa(200, COTIZACION))
    respuesta = client.get("/dashboard/api/dolar")
    assert respuesta.status_code == 200
    assert respuesta.get_json()["sell"] == 1050.0


def test_ruta_json_sin_cotizacion(client, monkeypatch):
    monkeypatch.setattr(exchange_rate.requests, "get", lambda *a, **k: RespuestaFalsa(500))
    respuesta = client.get("/dashboard/api/dolar")
    assert respuesta.status_code == 503
