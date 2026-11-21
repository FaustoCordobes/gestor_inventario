from app import create_app
from app.extensions import bcrypt, db
from app.models import User

app = create_app()

PASSWORD = "password123"

USERS = [
    ("Emma Johnson", "emma.johnson@example.com"),
    ("Liam Smith", "liam.smith@example.com"),
    ("Olivia Brown", "olivia.brown@example.com"),
    ("Noah Davis", "noah.davis@example.com"),
    ("Ava Wilson", "ava.wilson@example.com"),
    ("James Taylor", "james.taylor@example.com"),
    ("Sophia Clark", "sophia.clark@example.com"),
    ("Mason Lee", "mason.lee@example.com"),
    ("Isabella Moore", "isabella.moore@example.com"),
    ("Ethan Hall", "ethan.hall@example.com"),
]


def seed_users():
    with app.app_context():
        created = 0
        for name, email in USERS:
            if User.query.filter_by(email=email).first():
                continue
            password_hash = bcrypt.generate_password_hash(PASSWORD).decode("utf-8")
            db.session.add(User(name=name, email=email, password_hash=password_hash))
            created += 1
        db.session.commit()
        print(f"Users created: {created}")


if __name__ == "__main__":
    seed_users()
