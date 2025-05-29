from sqlalchemy import Column, DateTime, Integer, String, func
from database.db_config import Base


class User(Base):

    # A good habit to have since you do not want any surprises from the ORM's naming conventions.
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="guest", nullable=False)
    # We are not using datetime.now() here since the DB is more authorative.
    # Hence we give this responsibility to the DB instead of the backend.
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', role='{self.role}')>"
