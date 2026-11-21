from seeds.seed_users import seed_users
from seeds.seed_categories import seed_categories
from seeds.seed_suppliers import seed_suppliers
from seeds.seed_products import seed_products


def seed_all():
    seed_users()
    seed_categories()
    seed_suppliers()
    seed_products()


if __name__ == "__main__":
    seed_all()
