import plotly.graph_objects as go
from flask import Blueprint, jsonify, render_template
from flask_login import login_required
from sqlalchemy import func

from app.extensions import db
from app.models import Category, Product, Supplier
from app.services.exchange_rate import get_dollar_rate

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
        marker_color="#1c1c1e",
    ))
    fig.update_layout(
        autosize=True,
        height=320,
        margin=dict(l=8, r=8, t=16, b=8),
        yaxis_title="Valor a costo ($)",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    # automargin deja que Plotly reserve el espacio justo para títulos y etiquetas,
    # así nada se corta en pantallas angostas.
    fig.update_xaxes(automargin=True, tickangle=-30)
    fig.update_yaxes(automargin=True, tickprefix="$", title_standoff=8)
    return fig.to_html(
        full_html=False,
        include_plotlyjs="cdn",
        default_width="100%",
        config={"displayModeBar": False, "responsive": True},
    )


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
    dollar = get_dollar_rate()
    inventory_value_usd = inventory_value / dollar["sell"] if dollar and dollar["sell"] > 0 else None

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
        dollar=dollar,
        inventory_value_usd=inventory_value_usd,
    )


@dashboard_bp.route("/api/dolar")
@login_required
def dollar_api():
    dollar = get_dollar_rate()
    if dollar is None:
        return jsonify({"error": "No se pudo obtener la cotización del dólar."}), 503
    return jsonify(dollar)
