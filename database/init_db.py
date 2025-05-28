from database.db import create_user, get_user_by_username
from database.db_config import Base, SessionLocal, db

from utils.auth_utils import hash_password


def init_db():

    # Creates a database if it doesn't already exist.
    # Seeds the database with an initial admin user.

    print("Attempting to initialize database tables...")

    # IMPORTANT: Base.metadata.create_all() does NOT drop or recreate existing tables.
    # It only creates tables if they are missing.
    Base.metadata.create_all(bind=db)
    print("Database tables checked/created.")

    session = SessionLocal()
    try:
        # Checks if initial user exists else it will seed it.
        admin_user = get_user_by_username(session, "admin")

        if not admin_user:
            print("Creating initial 'admin' user...")
            hashed_password = hash_password("admin_password")
            create_user(session, "admin", hashed_password, "admin")
            print("'admin' user created successfully.")
        else:
            print("'admin' user already exists. Skipping creation.")
    except Exception as e:
        # If any error occurs during seeding rollback the transaction to ensure data integrity.
        session.rollback()
        print(f"Error during database initialization or admin user creation: {e}")
        raise
    finally:
        # Always close the database session to release the connection back to the pool.
        # This is crucial to prevent resource leaks.
        session.close()


if __name__ == "__main__":
    init_db()
    print("Database initialization script finished.")
