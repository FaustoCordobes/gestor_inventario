from sqlalchemy import func

from mcp_inventario.core import flask_app, mcp
from app.extensions import db
from app.models import Product, Supplier


@mcp.tool()
def dashboard_summary() -> dict:
    """Resumen del dashboard: total de productos, productos con stock bajo, valor del inventario a costo y proveedores activos."""
    with flask_app.app_context():
        inventory_value = db.session.query(func.sum(Product.cost * Product.stock)).scalar() or 0
        return {
            "total_productos": Product.query.count(),
            "productos_stock_bajo": Product.query.filter(Product.stock <= Product.min_stock).count(),
            "valor_inventario_costo": round(inventory_value, 2),
            "proveedores_activos": Supplier.query.filter_by(is_active=True).count(),
        }
