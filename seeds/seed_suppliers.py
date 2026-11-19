from app import create_app
from extensions import db
from models import Supplier

app = create_app()

SUPPLIERS = [
    ("Sportline Distribution", "Mendez", "Distributor", "+54 11 4555-1001", "sales@sportline.example", "Av. Corrientes 1200, Buenos Aires", "Running and sports apparel", True),
    ("Urban Textiles", "Ruiz", "Textile manufacturer", "+54 11 4555-1002", "orders@urbantextiles.example", "Av. Rivadavia 500, Buenos Aires", "Basic tees and hoodies", True),
    ("Denim Co", "Soto", "Denim manufacturer", "+54 11 4555-1003", "contact@denimco.example", "Calle Lavalle 900, Buenos Aires", "Jeans and denim jackets", True),
    ("Northwind Outdoor", "Perez", "Outdoor gear importer", "+54 11 4555-1004", "info@northwind.example", "Ruta 8 km 40, Pilar", "Jackets and fleece", True),
    ("Leather Works", "Diaz", "Leather goods workshop", "+54 11 4555-1005", "hello@leatherworks.example", "Calle Sarmiento 300, Quilmes", "Belts and leather accessories", True),
    ("Global Sports Imports", "Torres", "Importer", "+54 11 4555-1006", "import@globalsports.example", "Puerto Madero 77, Buenos Aires", "Imported sportswear", True),
    ("Cotton Mill SA", "Ibarra", "Cotton mill", "+54 11 4555-1007", "sales@cottonmill.example", "Parque Industrial, Tigre", "Raw cotton fabric", True),
    ("Hat Makers Co", "Herrera", "Hat workshop", "+54 11 4555-1009", "hats@hatmakers.example", "Calle Ayacucho 150, Moron", "Caps and hats", True),
    ("Retro Warehouse", "Ortiz", "Vintage wholesaler", "+54 11 4555-1008", "stock@retrowarehouse.example", "Av. San Martin 4100, Buenos Aires", "Vintage clothing, no longer active", False),
    ("Old Stock Outlet", "Vargas", "Liquidation outlet", None, None, None, "Closed, kept for history", False),
]


def seed_suppliers():
    with app.app_context():
        created = 0
        for name, last_name, type_supplier, phone, email, address, description, is_active in SUPPLIERS:
            if Supplier.query.filter_by(name=name).first():
                continue
            db.session.add(Supplier(
                name=name,
                last_name=last_name,
                type_supplier=type_supplier,
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
