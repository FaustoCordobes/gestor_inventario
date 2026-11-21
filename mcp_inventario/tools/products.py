from mcp_inventario.core import flask_app, mcp
from mcp_inventario.serializers import product_to_dict
from app.models import Product


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
