import pytest

from app.config import _database_url


@pytest.mark.parametrize("entrada", [
    "postgres://usuario:clave@host/base",
    "postgresql://usuario:clave@host/base",
])
def test_url_de_postgres_usa_psycopg2(monkeypatch, entrada):
    monkeypatch.setenv("DATABASE_URL", entrada)

    assert _database_url() == "postgresql+psycopg2://usuario:clave@host/base"


def test_sqlite_se_deja_igual(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite:///inventario.db")

    assert _database_url() == "sqlite:///inventario.db"


def test_url_con_driver_explicito_no_se_toca(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg2://usuario:clave@host/base")

    assert _database_url() == "postgresql+psycopg2://usuario:clave@host/base"
