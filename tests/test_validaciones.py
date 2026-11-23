import pytest

from app import create_app
from app.extensions import db
from app.models import Category, Product, Supplier


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


def post_new(client, category, **changes):
    response = client.post("/inventory/new", data=product_data(category, **changes))
    return response.get_data(as_text=True)


def test_letras_en_campos_numericos(client, category):
    html = post_new(client, category, price="abc", stock="diez", min_stock="x")

    assert "El precio tiene que ser un número." in html
    assert "El stock tiene que ser un número entero." in html
    assert "El stock mínimo tiene que ser un número entero." in html
    assert Product.query.count() == 0


def test_stock_negativo_y_decimal(client, category):
    assert "El stock no puede ser negativo." in post_new(client, category, stock="-3")
    assert "El stock tiene que ser un número entero." in post_new(client, category, stock="2.5")
    assert Product.query.count() == 0


def test_numeros_demasiado_grandes(client, category):
    html = post_new(client, category, stock="1" + "0" * 30, price="1e308")

    assert "El stock no puede ser mayor a 1.000.000." in html
    assert "El precio tiene que ser un número." in html
    assert Product.query.count() == 0


def test_precio_con_separador_de_miles_se_rechaza(client, category):
    html = post_new(client, category, price="1.000")

    assert "El precio puede tener hasta 2 decimales" in html
    assert Product.query.count() == 0


def test_categoria_con_caracter_raro_no_rompe(client, category):
    response = client.post("/inventory/new", data=product_data(category, category_id="²"))

    assert response.status_code == 200
    assert "Elegí una categoría de la lista." in response.get_data(as_text=True)
    assert Product.query.count() == 0


def test_precio_alto_no_se_redondea_al_editar(client, category):
    client.post("/inventory/new", data=product_data(category, price="1234567.5"))
    product = Product.query.one()

    html = client.get(f"/inventory/{product.id}/edit").get_data(as_text=True)
    assert 'value="1234567.5"' in html

    client.post(f"/inventory/{product.id}/edit", data=product_data(category, price="1234567.5", stock="7"))
    db.session.expire_all()
    product = Product.query.one()
    assert product.price == 1234567.5
    assert product.stock == 7


def test_editar_producto_con_proveedor_inactivo_no_lo_pierde(client, category):
    supplier = Supplier(supplier_type="Other", name="Proveedor viejo", is_active=False)
    db.session.add(supplier)
    db.session.commit()
    client.post("/inventory/new", data=product_data(category, supplier_id=str(supplier.id)))
    product = Product.query.one()

    html = client.get(f"/inventory/{product.id}/edit").get_data(as_text=True)
    assert "Proveedor viejo (inactivo)" in html

    client.post(
        f"/inventory/{product.id}/edit",
        data=product_data(category, supplier_id=str(supplier.id), stock="9"),
    )
    db.session.expire_all()
    assert Product.query.one().supplier_id == supplier.id


def test_proveedor_rechaza_telefono_con_letras(client):
    response = client.post("/supplier/new", data={
        "supplier_type": "Other",
        "name": "Proveedor Test",
        "phone": "abc",
    })

    assert "El teléfono solo puede tener números" in response.get_data(as_text=True)
    assert Supplier.query.count() == 0


def test_registro_rechaza_contrasena_demasiado_larga(client):
    client.get("/auth/logout")
    response = client.post("/auth/register", data={
        "name": "Beto",
        "email": "beto@mail.com",
        "password": "a" * 80,
        "confirmation": "a" * 80,
    })

    assert "demasiado larga" in response.get_data(as_text=True)


# --- Errores de campo: cada mensaje aparece debajo de su campo ---

def test_errores_de_producto_aparecen_en_cada_campo(client, category):
    html = post_new(client, category, price="abc", stock="", code="")

    for campo in ("price", "stock", "code"):
        assert f'id="{campo}-error"' in html
        assert f'aria-describedby="{campo}-error"' in html
    # El nombre está bien: no lleva error
    assert 'id="name-error"' not in html
    # Los errores de validación ya no van en un mensaje general arriba
    assert "message-error" not in html


def test_error_de_categoria_aparece_junto_al_campo(client):
    html = client.post("/inventory/categories", data={"name": ""}).get_data(as_text=True)

    assert 'id="name-error"' in html
    assert "El nombre de la categoría es obligatorio." in html
    assert "message-error" not in html


def test_errores_de_proveedor_aparecen_en_cada_campo(client):
    html = client.post("/supplier/new", data={
        "supplier_type": "", "name": "", "email": "no-es-un-email",
    }).get_data(as_text=True)

    for campo in ("supplier_type", "name", "email"):
        assert f'id="{campo}-error"' in html
    assert "message-error" not in html


def test_errores_de_registro_aparecen_en_cada_campo(app):
    anonimo = app.test_client()
    html = anonimo.post("/auth/register", data={
        "name": "Ana", "email": "no-es-un-email", "password": "123", "confirmation": "999",
    }).get_data(as_text=True)

    assert 'id="email-error"' in html
    assert 'id="password-error"' in html
    assert 'id="name-error"' not in html
    