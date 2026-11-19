from app import app
from extensions import db
from models import Category, Product


def seeder():
    with app.app_context():
        db.create_all()
        zapatillas = Category(name="Zapatillas")
        remeras = Category(name="Remeras")
        pantalones = Category(name="Pantalones")
        gorras = Category(name="Gorras")
        camperas = Category(name="Camperas")

        db.session.add_all([zapatillas, remeras, pantalones, gorras, camperas])
        db.session.flush()
        db.session.add_all([
            Product(code="ZAP-001", name="Zapatillas NewBalance", price="250000", cost="150000", stock="20", min_stock="5", category=zapatillas,
                    supplier=None)])
        db.session.commit()
        print("Base de datos seedeada correctamente")

if __name__ == "__main__":
    seeder()