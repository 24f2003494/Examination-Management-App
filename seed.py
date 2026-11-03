
from werkzeug.security import generate_password_hash

from app import app
from extensions import db
from models import User


ADMIN_NAME = "System Admin"
ADMIN_EMAIL = "admin@emp.com"

# Change this password before running the script.
ADMIN_PASSWORD = "Admin@12345"


def create_admin():

    with app.app_context():

        db.create_all()

        existing_admin = User.query.filter_by(
            email=ADMIN_EMAIL
        ).first()

        if existing_admin:
            print("Admin account already exists.")
            return

        admin = User()

        admin.full_name = ADMIN_NAME
        admin.email = ADMIN_EMAIL
        admin.password_hash = generate_password_hash(ADMIN_PASSWORD)
        admin.role = "admin"
        admin.is_approved = True

        db.session.add(admin)
        db.session.commit()

        print("Admin account created successfully.")


if __name__ == "__main__":
    create_admin()
