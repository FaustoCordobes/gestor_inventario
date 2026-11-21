import pytest

from app import create_app
from app.extensions import db
from app.models import Category, Product


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


@pytest.fixture
def category(app):
    category = Category(name="Bebidas")
    db.session.add(category)
    db.session.commit()
    return category


def product_data(category, **changes):
    data = {
        "code": "BEB-001",
        "name": "Agua mineral",
        "description": "",
        "price": "1200",
        "cost": "800",
        "stock": "20",
        "min_stock": "5",
        "category_id": str(category.id),
        "supplier_id": "",
    }
    data.update(changes)
    return data


def test_alta_de_producto_aparece_en_el_listado_con_stock_bajo(client, category):
    client.post("/inventory/new", data=product_data(category, stock="2"))

    assert Product.query.count() == 1
    html = client.get("/inventory/").get_data(as_text=True)
    assert "Agua mineral" in html
    assert "Stock bajo" in html


def test_rechaza_campos_vacios_y_numeros_negativos(client, category):
    response = client.post("/inventory/new", data=product_data(category, name="", price="-10"))
    html = response.get_data(as_text=True)

    assert "El nombre es obligatorio." in html
    assert "El precio no puede ser negativo." in html
    assert Product.query.count() == 0


def test_rechaza_codigo_duplicado(client, category):
    client.post("/inventory/new", data=product_data(category))
    response = client.post(
        "/inventory/new",
        data=product_data(category, code="beb-001", name="Gaseosa"),
    )

    assert "Ya existe un producto con ese código." in response.get_data(as_text=True)
    assert Product.query.count() == 1


def test_categoria_con_productos_no_se_elimina(client, category):
    client.post("/inventory/new", data=product_data(category))
    empty = Category(name="Limpieza")
    db.session.add(empty)
    db.session.commit()

    client.post(f"/inventory/categories/{category.id}/delete")
    assert db.session.get(Category, category.id) is not None

    client.post(f"/inventory/categories/{empty.id}/delete")
    assert db.session.get(Category, empty.id) is None
