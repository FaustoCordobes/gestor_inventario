from sqlalchemy import func

from app.blueprints.inventory import _validate_product
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
        product = Product.query.filter_by(code=codigo.strip()).first()
        if product is None:
            raise ValueError(f"No existe un producto con código {codigo}.")
        return product_to_dict(product)


@mcp.tool()
def low_stock() -> list[dict]:
    """Lista los productos con stock igual o menor al stock mínimo, ordenados por stock."""
    with flask_app.app_context():
        return [product_to_dict(p) for p in Product.query.order_by(Product.stock).all() if p.is_low_stock()]


@mcp.tool()
def list_categories() -> list[str]:
    """Lista los nombres de las categorías disponibles, para usarlos al crear un producto."""
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
        supplier_name = proveedor.strip()
        if supplier_name:
            # Reutiliza la validación del formulario web, que pide el id del proveedor.
            supplier_id = str(_find_supplier(supplier_name).id)
        else:
            supplier_id = ""

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

        product = Product(**clean)
        try:
            db.session.add(product)
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise ValueError("No se pudo guardar el producto. Probá de nuevo.")
        return product_to_dict(product)
