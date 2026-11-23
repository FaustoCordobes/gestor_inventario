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


@pytest.fixture(autouse=True)
def cache_vacia():
    exchange_rate.clear_cache()
    yield
    exchange_rate.clear_cache()


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


class RelojFalso:
    def __init__(self):
        self.ahora = 1000.0

    def monotonic(self):
        return self.ahora


@pytest.fixture
def reloj(monkeypatch):
    reloj = RelojFalso()
    monkeypatch.setattr(exchange_rate, "time", reloj)
    return reloj


def contar_pedidos(monkeypatch, respuesta):
    pedidos = []

    def get(*args, **kwargs):
        pedidos.append(1)
        if isinstance(respuesta, Exception):
            raise respuesta
        return respuesta

    monkeypatch.setattr(exchange_rate.requests, "get", get)
    return pedidos


def test_segunda_consulta_usa_la_cotizacion_guardada(monkeypatch, reloj):
    pedidos = contar_pedidos(monkeypatch, RespuestaFalsa(200, COTIZACION))

    assert exchange_rate.get_dollar_rate()["sell"] == 1050.0
    reloj.ahora += exchange_rate.CACHE_SEGUNDOS - 1
    assert exchange_rate.get_dollar_rate()["sell"] == 1050.0

    assert len(pedidos) == 1


def test_pasado_el_tiempo_se_consulta_de_nuevo(monkeypatch, reloj):
    pedidos = contar_pedidos(monkeypatch, RespuestaFalsa(200, COTIZACION))

    exchange_rate.get_dollar_rate()
    reloj.ahora += exchange_rate.CACHE_SEGUNDOS + 1
    exchange_rate.get_dollar_rate()

    assert len(pedidos) == 2


def test_si_la_api_falla_se_sigue_mostrando_la_ultima_cotizacion(monkeypatch, reloj):
    contar_pedidos(monkeypatch, RespuestaFalsa(200, COTIZACION))
    exchange_rate.get_dollar_rate()

    reloj.ahora += exchange_rate.CACHE_SEGUNDOS + 1
    contar_pedidos(monkeypatch, requests.Timeout("tardó demasiado"))

    assert exchange_rate.get_dollar_rate()["sell"] == 1050.0


def test_tras_un_error_no_se_reintenta_en_cada_visita(monkeypatch, reloj):
    pedidos = contar_pedidos(monkeypatch, requests.ConnectionError("sin internet"))

    assert exchange_rate.get_dollar_rate() is None
    reloj.ahora += exchange_rate.REINTENTO_TRAS_ERROR_SEGUNDOS - 1
    assert exchange_rate.get_dollar_rate() is None
    assert len(pedidos) == 1

    reloj.ahora += 2
    exchange_rate.get_dollar_rate()
    assert len(pedidos) == 2


def test_dashboard_no_consulta_la_api_en_cada_visita(client, monkeypatch, reloj):
    pedidos = contar_pedidos(monkeypatch, RespuestaFalsa(200, COTIZACION))

    for _ in range(3):
        assert client.get("/dashboard/").status_code == 200

    assert len(pedidos) == 1
