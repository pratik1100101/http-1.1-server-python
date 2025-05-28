import os
from dotenv import load_dotenv
import sqlalchemy as sa
from sqlalchemy import orm as so, text
import psycopg2


# Load the environment variable for database URL
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is not set.")

# Define the database as db, echo is False since we are in prod and pool_recycle is
# set to reset connection every 1 hr to avoid database server closing idle connection due to timeout.
db = sa.create_engine(DATABASE_URL, echo=False, pool_recycle=3600)

# Define a base class for declarative models that all model classes must inherit.
# It's the foundation upon which your ORM classes are built, allowing them to be mapped to database tables.
Base = so.declarative_base()

# Creates a session factory which allows us to create a new session everytime by calling it.
SessionLocal = so.sessionmaker(autoflush=False, bind=db)


def start_db():
    # Create a new session from the session facttory I mentioned above.
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
