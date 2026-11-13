
from getpass import getpass

from app import app
from extensions import db
from models.user import User
from werkzeug.security import generate_password_hash


def create_admin():
    print("\n--- Create Admin Account ---")

    full_name = input("Enter admin name: ").strip()
    email = input("Enter admin email: ").strip().lower()
    password = getpass("Enter admin password: ")
    confirm_password = getpass("Confirm admin password: ")

    if not full_name or not email or not password:
        print("All fields are required.")
        return

    if password != confirm_password:
        print("Passwords do not match.")
        return

    with app.app_context():
        existing_user = User.query.filter_by(email=email).first()

        if existing_user:
            print("An account with this email already exists.")
            return

        admin = User(
            full_name=full_name,
            email=email,
            password_hash=generate_password_hash(password),
            role="admin",
            is_approved=True
        )

        try:
            db.session.add(admin)
            db.session.commit()
            print("\nAdmin account created successfully!")
            print("Email:", email)
        except Exception as error:
            db.session.rollback()
            print("Unable to create admin account:", error)


if __name__ == "__main__":
    create_admin()
