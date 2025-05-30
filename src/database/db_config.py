from contextlib import contextmanager
import os
from dotenv import load_dotenv
import sqlalchemy as sa
from sqlalchemy import orm as so
import psycopg2


# Load the environment variable for database URL
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL", "")
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


# The @contextmanager decorator allows us to use a generator function with the 'with' statement.
# Normally, generator functions can't be used in 'with' blocks because their returned generator objects
# don't implement the __enter__ and __exit__ dunders required by the context manager protocol in 'with'.
# The 'with' statement essentially wraps code in a try/finally block for safe resource management:
# __enter__() - sets up the resource (runs before the block)
# __exit__() - tears it down (runs after the block, even if there's an exception)
@contextmanager
def start_db():
    # Create a new session from the session factory I mentioned above.
    session = SessionLocal()
    try:
        # Yield gives the session to the calling block of code and waits for it to exceute.
        # Once it has finished executing the control resumes here and we move to the finally statement.
        # If there is any exception in the code calling this, it is passed back here and we just
        # close the session. The errors will be handled by the functions calling this.
        yield session
    finally:
        session.close()
