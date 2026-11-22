from sqlalchemy import func

from app.blueprints.supplier import _supplier_form_data, _validate_supplier
from app.extensions import db
from app.models import Supplier
from mcp_inventario.core import flask_app, mcp
from mcp_inventario.serializers import product_to_dict, supplier_to_dict


def _find_supplier(nombre):
    supplier = Supplier.query.filter(func.lower(Supplier.name) == nombre.strip().lower()).first()
    if supplier is None:
        raise ValueError(f"No existe un proveedor llamado {nombre}.")
    return supplier


def _save_supplier(supplier, data):
    supplier.supplier_type = data["supplier_type"]
    supplier.name = data["name"]
    supplier.contact_name = data["contact_name"] or None
    supplier.phone = data["phone"] or None
    supplier.email = data["email"] or None
    supplier.address = data["address"] or None
    supplier.description = data["description"] or None
    supplier.is_active = data["is_active"]
    try:
        db.session.add(supplier)
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise ValueError("No se pudo guardar el proveedor. Probá de nuevo.")
    return supplier_to_dict(supplier)


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

        return _save_supplier(Supplier(), data)


@mcp.tool()
def update_supplier(
    nombre: str,
    nuevo_nombre: str | None = None,
    tipo: str | None = None,
    contacto: str | None = None,
    telefono: str | None = None,
    email: str | None = None,
    direccion: str | None = None,
    descripcion: str | None = None,
    activo: bool | None = None,
) -> dict:
    """Edita un proveedor buscado por su nombre exacto. Solo cambia los campos que se pasan; los omitidos quedan igual. Para vaciar un campo de texto, pasar una cadena vacía. Devuelve el proveedor actualizado."""
    with flask_app.app_context():
        supplier = _find_supplier(nombre)
        data = _supplier_form_data(supplier)

        if nuevo_nombre is not None:
            data["name"] = nuevo_nombre.strip()
        if tipo is not None:
            data["supplier_type"] = tipo.strip()
        if contacto is not None:
            data["contact_name"] = contacto.strip()
        if telefono is not None:
            data["phone"] = telefono.strip()
        if email is not None:
            data["email"] = email.strip()
        if direccion is not None:
            data["address"] = direccion.strip()
        if descripcion is not None:
            data["description"] = descripcion.strip()
        if activo is not None:
            data["is_active"] = activo

        errors = _validate_supplier(data, supplier_id=supplier.id)
        if errors:
            raise ValueError(" ".join(errors))
        return _save_supplier(supplier, data)


@mcp.tool()
def delete_supplier(nombre: str) -> dict:
    """Elimina un proveedor buscado por su nombre exacto. Sus productos no se borran: quedan sin proveedor, igual que en la web."""
    with flask_app.app_context():
        supplier = _find_supplier(nombre)
        name = supplier.name
        try:
            db.session.delete(supplier)
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise ValueError("No se pudo eliminar el proveedor. Probá de nuevo.")
        return {"eliminado": True, "nombre": name}
