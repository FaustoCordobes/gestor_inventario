import plotly.graph_objects as go
from flask import Blueprint, render_template
from flask_login import login_required
from sqlalchemy import func

from extensions import db
from models import Category, Product, Supplier

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")

STOCK_VALUE = Product.cost * Product.stock


def _category_chart():
    rows = (
        db.session.query(Category.name, func.sum(STOCK_VALUE))
        .join(Category.products)
        .group_by(Category.id, Category.name)
        .order_by(func.sum(STOCK_VALUE).desc())
        .all()
    )
    if not rows:
        return None

    fig = go.Figure(go.Bar(
        x=[name for name, _ in rows],
        y=[round(total or 0, 2) for _, total in rows],
        marker_color="#3b82f6",
    ))
    fig.update_layout(
        height=320,
        margin=dict(l=40, r=20, t=20, b=40),
        yaxis_title="Valor a costo ($)",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    return fig.to_html(full_html=False, include_plotlyjs="cdn", config={"displayModeBar": False})


def _top_suppliers(limit=4):
    result = []
    for supplier in Supplier.query.all():
        value = sum(p.cost * p.stock for p in supplier.products)
        result.append({"supplier": supplier, "value": value, "products": len(supplier.products)})
    result.sort(key=lambda row: row["value"], reverse=True)
    return result[:limit]


@dashboard_bp.route("/")
@login_required
def index():
    total_products = Product.query.count()
    low_stock = Product.query.filter(Product.stock <= Product.min_stock).order_by(Product.stock).all()
    inventory_value = db.session.query(func.sum(STOCK_VALUE)).scalar() or 0
    active_suppliers = Supplier.query.filter_by(is_active=True).count()
    featured = Product.query.order_by(STOCK_VALUE.desc()).limit(5).all()

    return render_template(
        "dashboard/index.html",
        total_products=total_products,
        low_stock_count=len(low_stock),
        inventory_value=inventory_value,
        active_suppliers=active_suppliers,
        chart_html=_category_chart(),
        top_suppliers=_top_suppliers(),
        featured=featured,
        low_stock=low_stock,
    )
