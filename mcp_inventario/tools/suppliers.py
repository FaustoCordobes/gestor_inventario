from sqlalchemy import func

from mcp_inventario.core import flask_app, mcp
from mcp_inventario.serializers import product_to_dict, supplier_to_dict
from app.models import Supplier


def _find_supplier(nombre):
    supplier = Supplier.query.filter(func.lower(Supplier.name) == nombre.strip().lower()).first()
    if supplier is None:
        raise ValueError(f"No existe un proveedor llamado {nombre}.")
    return supplier


@mcp.tool()
def list_suppliers(buscar: str = "") -> list[dict]:
    """Lista los proveedores ordenados por nombre. Si se pasa `buscar`, filtra por nombre."""
    with flask_app.app_context():
        query = Supplier.query

        if buscar.strip():
            query = query.filter(Supplier.name.icontains(buscar.strip(), autoescape=True))
        return [supplier_to_dict(s) for s in query.order_by(Supplier.name).all()]


@mcp.tool()
def supplier_detail(nombre: str) -> dict:
    """Devuelve los datos de un proveedor buscado por su nombre exacto (sin distinguir mayúsculas)."""
    with flask_app.app_context():
        return supplier_to_dict(_find_supplier(nombre))


@mcp.tool()
def supplier_products(nombre: str) -> list[dict]:
    """Lista los productos que provee un proveedor, buscado por su nombre exacto."""
    with flask_app.app_context():
        supplier = _find_supplier(nombre)
        return [product_to_dict(p) for p in sorted(supplier.products, key=lambda p: p.name)]
