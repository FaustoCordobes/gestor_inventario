import pytest

from app import create_app
from extensiones import db
from models import Categoria, Producto


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
    cliente = app.test_client()
    cliente.post("/auth/registro", data={
        "nombre": "Ana",
        "email": "ana@mail.com",
        "password": "clave123",
        "confirmacion": "clave123",
    })
    cliente.post("/auth/login", data={"email": "ana@mail.com", "password": "clave123"})
    return cliente


@pytest.fixture
def categoria(app):
    categoria = Categoria(nombre="Bebidas")
    db.session.add(categoria)
    db.session.commit()
    return categoria


def datos_producto(categoria, **cambios):
    datos = {
        "codigo": "BEB-001",
        "nombre": "Agua mineral",
        "descripcion": "",
        "precio": "1200",
        "costo": "800",
        "stock": "20",
        "stock_minimo": "5",
        "categoria_id": str(categoria.id),
        "proveedor_id": "",
    }
    datos.update(cambios)
    return datos


def test_alta_de_producto_aparece_en_el_listado_con_stock_bajo(cliente, categoria):
    cliente.post("/inventario/nuevo", data=datos_producto(categoria, stock="2"))

    assert Producto.query.count() == 1
    html = cliente.get("/inventario/").get_data(as_text=True)
    assert "Agua mineral" in html
    assert "Stock bajo" in html


def test_rechaza_campos_vacios_y_numeros_negativos(cliente, categoria):
    respuesta = cliente.post("/inventario/nuevo", data=datos_producto(categoria, nombre="", precio="-10"))
    html = respuesta.get_data(as_text=True)

    assert "El nombre es obligatorio." in html
    assert "El precio no puede ser negativo." in html
    assert Producto.query.count() == 0


def test_rechaza_codigo_duplicado(cliente, categoria):
    cliente.post("/inventario/nuevo", data=datos_producto(categoria))
    respuesta = cliente.post(
        "/inventario/nuevo",
        data=datos_producto(categoria, codigo="beb-001", nombre="Gaseosa"),
    )

    assert "Ya existe un producto con ese código." in respuesta.get_data(as_text=True)
    assert Producto.query.count() == 1


def test_categoria_con_productos_no_se_elimina(cliente, categoria):
    cliente.post("/inventario/nuevo", data=datos_producto(categoria))
    vacia = Categoria(nombre="Limpieza")
    db.session.add(vacia)
    db.session.commit()

    cliente.post(f"/inventario/categorias/{categoria.id}/eliminar")
    assert db.session.get(Categoria, categoria.id) is not None

    cliente.post(f"/inventario/categorias/{vacia.id}/eliminar")
    assert db.session.get(Categoria, vacia.id) is None
