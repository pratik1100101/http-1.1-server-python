from database.db import create_user, get_user_by_username
from database.db_config import Base, SessionLocal, db
import sqlalchemy.orm as so

from utils.auth_utils import hash_password


def init_db():
    print("Attempting to initialize database tables...")

    Base.metadata.create_all(bind=db)
    print("Database tables checked/created.")

    session: so.Session = SessionLocal()
    try:
        admin_user = get_user_by_username(session, "admin")

        if not admin_user:
            print("Creating initial 'admin' user...")
            hashed_password = hash_password("admin_password")
            create_user(session, "admin", hashed_password, "admin")
            print("'admin' user created successfully.")
        else:
            print("'admin' user already exists. Skipping creation.")
    except Exception as e:
        session.rollback()
        print(f"Error during database initialization or admin user creation: {e}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    init_db()
    print("Database initialization script finished.")
