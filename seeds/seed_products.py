from app import create_app
from extensions import db
from models import Category, Product, Supplier

app = create_app()

PRODUCTS = [
    ("SNK-001", "Air Runner Sneakers", "Lightweight running sneakers", 85000, 52000, 14, 5, "Sneakers", "Sportline Distribution"),
    ("SNK-002", "Court Classic White", "White leather court sneakers", 98000, 61000, 3, 5, "Sneakers", "Sportline Distribution"),
    ("TSH-001", "Basic Cotton T-Shirt", "Black 100% cotton tee", 18000, 8000, 40, 10, "T-Shirts", "Urban Textiles"),
    ("TSH-002", "Graphic Print T-Shirt", "Front print design", 22000, 10500, 6, 8, "T-Shirts", "Cotton Mill SA"),
    ("JEA-001", "Slim Fit Jeans", "Dark wash slim jeans", 56000, 31000, 9, 4, "Jeans", "Denim Co"),
    ("JEA-002", "Straight Leg Jeans", "Classic straight leg jeans", 52000, 28000, 0, 4, "Jeans", None),
    ("PAN-001", "Chino Pants", "Beige cotton chinos", 45000, 24000, 12, 5, "Pants", "Denim Co"),
    ("HAT-001", "Snapback Cap", "Adjustable snapback cap", 15000, 6000, 25, 5, "Hats", "Hat Makers Co"),
    ("JAC-001", "Windbreaker Jacket", "Water-resistant windbreaker", 92000, 54000, 4, 3, "Jackets", "Northwind Outdoor"),
    ("JAC-002", "Vintage Denim Jacket", "Retro denim jacket", 78000, 40000, 0, 2, "Jackets", "Retro Warehouse"),
    ("HOO-001", "Fleece Hoodie", "Warm fleece pullover hoodie", 68000, 38000, 10, 5, "Hoodies", "Northwind Outdoor"),
    ("SOC-001", "Sports Socks 3-Pack", "Cotton blend socks", 9000, 3500, 60, 15, "Socks", "Sportline Distribution"),
    ("SHO-001", "Running Shorts", "Quick-dry running shorts", 26000, 12000, 2, 6, "Shorts", "Global Sports Imports"),
    ("ACC-001", "Brown Leather Belt", "Full grain leather belt", 24000, 11000, 18, 5, "Accessories", "Leather Works"),
]


def seed_products():
    with app.app_context():
        created = 0
        for code, name, description, price, cost, stock, min_stock, category_name, supplier_name in PRODUCTS:
            if Product.query.filter_by(code=code).first():
                continue
            category = Category.query.filter_by(name=category_name).one()
            supplier = None
            if supplier_name:
                supplier = Supplier.query.filter_by(name=supplier_name).one()
            db.session.add(Product(
                code=code,
                name=name,
                description=description,
                price=price,
                cost=cost,
                stock=stock,
                min_stock=min_stock,
                category=category,
                supplier=supplier,
            ))
            created += 1
        db.session.commit()
        print(f"Products created: {created}")


if __name__ == "__main__":
    seed_products()
