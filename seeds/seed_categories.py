from app import create_app
from extensions import db
from models import Category

app = create_app()

CATEGORY_NAMES = [
    "Sneakers",
    "T-Shirts",
    "Jeans",
    "Pants",
    "Hats",
    "Jackets",
    "Hoodies",
    "Socks",
    "Shorts",
    "Accessories",
]


def seed_categories():
    with app.app_context():
        created = 0
        for name in CATEGORY_NAMES:
            if Category.query.filter_by(name=name).first():
                continue
            db.session.add(Category(name=name))
            created += 1
        db.session.commit()
        print(f"Categories created: {created}")


if __name__ == "__main__":
    seed_categories()
