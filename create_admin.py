
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

    if len(full_name) < 2 or len(full_name) > 100:
        print("Name must contain 2 to 100 characters.")
        return

    if len(email) > 254 or "@" not in email or "." not in email.rsplit("@", 1)[-1]:
        print("Please enter a valid email address.")
        return

    if len(password) < 8 or len(password) > 128:
        print("Password must contain 8 to 128 characters.")
        return

    if not any(ch.isalpha() for ch in password) or not any(ch.isdigit() for ch in password):
        print("Password must contain at least one letter and one number.")
        return

    if password != confirm_password:
        print("Passwords do not match.")
        return

    with app.app_context():
        existing_user = User.query.filter_by(email=email).first()

        if existing_user:
            print("An account with this email already exists.")
            return

        admin = User()

        admin.full_name = full_name
        admin.email = email
        admin.password_hash = generate_password_hash(password)
        admin.role = "admin"
        admin.is_approved = True

        db.session.add(admin)
        db.session.commit()

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
