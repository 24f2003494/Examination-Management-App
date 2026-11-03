
from app import app
from extensions import db
from models import User

with app.app_context():

    inspector = db.inspect(db.engine)

    print("\nFOREIGN KEY VERIFICATION")
    print("-------------------------")

    for table_name in inspector.get_table_names():
        foreign_keys = inspector.get_foreign_keys(table_name)

        for fk in foreign_keys:
            print(
                f"{table_name}.{fk['constrained_columns']} "
                f"-> {fk['referred_table']}.{fk['referred_columns']}"
            )

    print("\nADMIN ACCOUNT VERIFICATION")
    print("-------------------------")

    admin = User.query.filter_by(
        email="admin@emp.com",
        role="admin"
    ).first()

    if admin:
        print("Admin account exists.")
        print("Admin name:", admin.full_name)
        print("Admin role:", admin.role)
        print("Admin approved:", admin.is_approved)
    else:
        print("Admin account not found!")

    print("\nVerification completed.")
