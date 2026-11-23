import asyncio

from mcp_inventario.auth import StaticTokenVerifier


def test_token_correcto_es_aceptado():
    acceso = asyncio.run(StaticTokenVerifier("clave-secreta").verify_token("clave-secreta"))

    assert acceso is not None
    assert acceso.client_id == "gestor-inventario"


def test_token_incorrecto_es_rechazado():
    assert asyncio.run(StaticTokenVerifier("clave-secreta").verify_token("otra-clave")) is None


def test_token_vacio_es_rechazado():
    assert asyncio.run(StaticTokenVerifier("clave-secreta").verify_token("")) is None
