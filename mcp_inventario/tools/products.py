from sqlalchemy import func

from app.blueprints.inventory import _product_form_data, _validate_product
from app.extensions import db
from app.models import Category, Product, Supplier
from mcp_inventario.core import flask_app, mcp
from mcp_inventario.serializers import product_to_dict


def _find_category(nombre):
    category = Category.query.filter(func.lower(Category.name) == nombre.strip().lower()).first()
    if category is None:
        raise ValueError(f"No existe una categoría llamada {nombre}.")
    return category


def _find_supplier(nombre):
    supplier = Supplier.query.filter(func.lower(Supplier.name) == nombre.strip().lower()).first()
    if supplier is None:
        raise ValueError(f"No existe un proveedor llamado {nombre}.")
    return supplier


def _find_product(codigo):
    product = Product.query.filter(func.lower(Product.code) == codigo.strip().lower()).first()
    if product is None:
        raise ValueError(f"No existe un producto con código {codigo}.")
    return product


def _save_product(product, clean):
    for field, value in clean.items():
        setattr(product, field, value)
    try:
        db.session.add(product)
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise ValueError("No se pudo guardar el producto. Probá de nuevo.")
    return product_to_dict(product)


@mcp.tool()
def list_products(buscar: str = "") -> list[dict]:
    """Lista los productos ordenados por nombre. Si se pasa `buscar`, filtra por nombre."""
    with flask_app.app_context():
        query = Product.query

        if buscar.strip():
            query = query.filter(Product.name.icontains(buscar.strip(), autoescape=True))
        return [product_to_dict(p) for p in query.order_by(Product.name).all()]


@mcp.tool()
def product_detail(codigo: str) -> dict:
    """Devuelve los datos de un producto buscado por su código (por ejemplo ZAP-001)."""
    with flask_app.app_context():
        return product_to_dict(_find_product(codigo))


@mcp.tool()
def low_stock() -> list[dict]:
    """Lista los productos con stock igual o menor al stock mínimo, ordenados por stock."""
    with flask_app.app_context():
        return [product_to_dict(p) for p in Product.query.order_by(Product.stock).all() if p.is_low_stock()]


@mcp.tool()
def list_categories() -> list[str]:
    """Lista los nombres de las categorías disponibles, para usarlos al crear o editar un producto."""
    with flask_app.app_context():
        return [c.name for c in Category.query.order_by(Category.name).all()]


@mcp.tool()
def create_product(
    codigo: str,
    nombre: str,
    precio: float,
    stock: int,
    categoria: str,
    costo: float = 0,
    stock_minimo: int = 5,
    descripcion: str = "",
    proveedor: str = "",
) -> dict:
    """Crea un producto. `categoria` y `proveedor` se indican por nombre (usar list_categories para ver las categorías; el proveedor es opcional). Devuelve el producto creado."""
    with flask_app.app_context():
        category = _find_category(categoria)
        supplier_id = str(_find_supplier(proveedor).id) if proveedor.strip() else ""

        data = {
            "code": codigo.strip(),
            "name": nombre.strip(),
            "description": descripcion.strip(),
            "price": str(precio),
            "cost": str(costo),
            "stock": str(stock),
            "min_stock": str(stock_minimo),
            "category_id": str(category.id),
            "supplier_id": supplier_id,
        }
        errors, clean = _validate_product(data)
        if errors:
            raise ValueError(" ".join(errors))

        return _save_product(Product(), clean)


@mcp.tool()
def update_product(
    codigo: str,
    nuevo_codigo: str | None = None,
    nombre: str | None = None,
    precio: float | None = None,
    stock: int | None = None,
    categoria: str | None = None,
    costo: float | None = None,
    stock_minimo: int | None = None,
    descripcion: str | None = None,
    proveedor: str | None = None,
) -> dict:
    """Edita un producto buscado por su código. Solo cambia los campos que se pasan; los que se omiten quedan igual. Para quitar la descripción o el proveedor, pasar una cadena vacía. Devuelve el producto actualizado."""
    with flask_app.app_context():
        product = _find_product(codigo)
        data = _product_form_data(product)

        if nuevo_codigo is not None:
            data["code"] = nuevo_codigo.strip()
        if nombre is not None:
            data["name"] = nombre.strip()
        if precio is not None:
            data["price"] = str(precio)
        if stock is not None:
            data["stock"] = str(stock)
        if categoria is not None:
            data["category_id"] = str(_find_category(categoria).id)
        if costo is not None:
            data["cost"] = str(costo)
        if stock_minimo is not None:
            data["min_stock"] = str(stock_minimo)
        if descripcion is not None:
            data["description"] = descripcion.strip()
        if proveedor is not None:
            data["supplier_id"] = str(_find_supplier(proveedor).id) if proveedor.strip() else ""

        errors, clean = _validate_product(data, product_id=product.id)
        if errors:
            raise ValueError(" ".join(errors))
        return _save_product(product, clean)


@mcp.tool()
def delete_product(codigo: str) -> dict:
    """Elimina un producto buscado por su código. Devuelve una confirmación con el código eliminado."""
    with flask_app.app_context():
        product = _find_product(codigo)
        nombre = product.name
        try:
            db.session.delete(product)
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise ValueError("No se pudo eliminar el producto. Probá de nuevo.")
        return {"eliminado": True, "codigo": codigo.strip(), "nombre": nombre}
