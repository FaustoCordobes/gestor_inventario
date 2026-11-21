from app import create_app
from app.extensions import db
from app.models import Supplier

app = create_app()

SUPPLIERS = [
    ("Sportline Distribution", "Mendez", "Distributor", "+54 11 4555-1001", "sales@sportline.example", "Av. Corrientes 1200, Buenos Aires", "Running and sports apparel", True),
    ("Urban Textiles", "Ruiz", "Manufacturer", "+54 11 4555-1002", "orders@urbantextiles.example", "Av. Rivadavia 500, Buenos Aires", "Basic tees and hoodies", True),
    ("Denim Co", "Soto", "Manufacturer", "+54 11 4555-1003", "contact@denimco.example", "Calle Lavalle 900, Buenos Aires", "Jeans and denim jackets", True),
    ("Northwind Outdoor", "Perez", "Importer", "+54 11 4555-1004", "info@northwind.example", "Ruta 8 km 40, Pilar", "Jackets and fleece", True),
    ("Leather Works", "Diaz", "Workshop", "+54 11 4555-1005", "hello@leatherworks.example", "Calle Sarmiento 300, Quilmes", "Belts and leather accessories", True),
    ("Global Sports Imports", "Torres", "Importer", "+54 11 4555-1006", "import@globalsports.example", "Puerto Madero 77, Buenos Aires", "Imported sportswear", True),
    ("Cotton Mill SA", "Ibarra", "Manufacturer", "+54 11 4555-1007", "sales@cottonmill.example", "Parque Industrial, Tigre", "Raw cotton fabric", True),
    ("Hat Makers Co", "Herrera", "Workshop", "+54 11 4555-1009", "hats@hatmakers.example", "Calle Ayacucho 150, Moron", "Caps and hats", True),
    ("Retro Warehouse", "Ortiz", "Wholesaler", "+54 11 4555-1008", "stock@retrowarehouse.example", "Av. San Martin 4100, Buenos Aires", "Vintage clothing, no longer active", False),
    ("Old Stock Outlet", "Vargas", "Other", None, None, None, "Closed, kept for history", False),
]


def seed_suppliers():
    with app.app_context():
        created = 0
        for name, contact_name, supplier_type, phone, email, address, description, is_active in SUPPLIERS:
            if Supplier.query.filter_by(name=name).first():
                continue
            db.session.add(Supplier(
                name=name,
                contact_name=contact_name,
                supplier_type=supplier_type,
                phone=phone,
                email=email,
                address=address,
                description=description,
                is_active=is_active,
            ))
            created += 1
        db.session.commit()
        print(f"Suppliers created: {created}")


if __name__ == "__main__":
    seed_suppliers()
