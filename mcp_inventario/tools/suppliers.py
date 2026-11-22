from sqlalchemy import func

from app.blueprints.supplier import _validate_supplier
from app.extensions import db
from app.models import Supplier
from mcp_inventario.core import flask_app, mcp
from mcp_inventario.serializers import product_to_dict, supplier_to_dict


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


@mcp.tool()
def create_supplier(
    nombre: str,
    tipo: str,
    contacto: str = "",
    telefono: str = "",
    email: str = "",
    direccion: str = "",
    descripcion: str = "",
    activo: bool = True,
) -> dict:
    """Crea un proveedor. `tipo` tiene que ser uno de: Distributor, Manufacturer, Importer, Workshop, Wholesaler, Other. Devuelve el proveedor creado."""
    with flask_app.app_context():
        data = {
            "supplier_type": tipo.strip(),
            "name": nombre.strip(),
            "contact_name": contacto.strip(),
            "phone": telefono.strip(),
            "email": email.strip(),
            "address": direccion.strip(),
            "description": descripcion.strip(),
            "is_active": activo,
        }
        errors = _validate_supplier(data)
        if errors:
            raise ValueError(" ".join(errors))

        supplier = Supplier(
            supplier_type=data["supplier_type"],
            name=data["name"],
            contact_name=data["contact_name"] or None,
            phone=data["phone"] or None,
            email=data["email"] or None,
            address=data["address"] or None,
            description=data["description"] or None,
            is_active=data["is_active"],
        )
        try:
            db.session.add(supplier)
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise ValueError("No se pudo guardar el proveedor. Probá de nuevo.")
        return supplier_to_dict(supplier)
