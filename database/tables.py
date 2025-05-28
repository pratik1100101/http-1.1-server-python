from typing import Dict
from database.models import User
from utils.auth_utils import hash_password


class UserTable:
    ROLES = {"admin", "user", "guest"}

    def __init__(self) -> None:
        self.users: Dict[str, User] = {}

    def add_user(self, username: str, password: str, role: str) -> None:
        if username in self.users:
            raise ValueError(f"User '{username}' already exists.")
        if role not in self.ROLES:
            raise ValueError(f"Role '{role}' doesn't exist.")

        hashed_password = hash_password(password)

        self.users[username] = User(
            username=username, hashed_password=hashed_password, role=role
        )

    def get_user_by_username(self, username: str) -> User:
        if username in self.users:
            return self.users[username]
        else:
            raise ValueError(f"User '{username}' doesn't exist.")
