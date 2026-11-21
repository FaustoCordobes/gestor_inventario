from mcp_inventario.core import flask_app, mcp
from app.models import Product


def _product_to_dict(product):

    return {
        "codigo": product.code,
        "nombre": product.name,
        "categoria": product.category.name,
        "proveedor": product.supplier.name if product.supplier else None,
        "precio": product.price,
        "costo": product.cost,
        "stock": product.stock,
        "stock_minimo": product.min_stock,
        "stock_bajo": product.is_low_stock(),
    }

@mcp.tool()
def list_products(buscar: str = "") -> list[dict]:
    with flask_app.app_context():
        query = Product.query

        if buscar.strip():
            query = query.filter(Product.name.icontains(buscar.strip(), autoescape=True))
        return [_product_to_dict(p) for p in query.order_by(Product.name).all()]

@mcp.tool()
def detail(codigo: str) -> dict:

    with flask_app.app_context():
        product = Product.query.filter_by(code=codigo.strip()).first()
        if product is None:

            raise ValueError(f"No existe un producto con código {codigo}.")
        return _product_to_dict(product)


@mcp.tool()
def low_stock() -> list[dict]:
    with flask_app.app_context():
        return [_product_to_dict(p) for p in Product.query.order_by(Product.stock).all() if p.is_low_stock()]




