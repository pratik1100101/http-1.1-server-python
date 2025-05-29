from typing import List, Optional

from database.models import User
import sqlalchemy.orm as so


def get_user_by_username(session: so.Session, username: str) -> Optional[User]:
    return session.query(User).filter(User.username == username).first()


def get_user_by_id(session: so.Session, id: int) -> Optional[User]:
    return session.query(User).filter(User.id == id).first()


def get_users(session: so.Session) -> List[User]:
    # We can add skip and limit later for pagination but I am choosing not to here.
    return session.query(User).all()


def create_user(
    session: so.Session, username: str, hashed_password: str, role: str = "guest"
) -> User:
    db_user = User(username=username, hashed_password=hashed_password, role=role)
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user


def update_user_role(session: so.Session, username: str, new_role: str) -> User:
    user = session.query(User).filter(User.username == username).first()
    if user:
        # Getting an error here since role is "Column[str]" and we are assinging "str" to it.
        # Happens when you have a static type checker, ignore it.
        user.role = new_role  # type: ignore
        session.commit()
        session.refresh(user)
    return user


def delete_user(session: so.Session, username: str) -> bool:
    user = session.query(User).filter(User.username == username).first()
    if user:
        session.delete(user)
        session.commit()
        return True
    return False
