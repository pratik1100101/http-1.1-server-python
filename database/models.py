from typing import TypedDict


class User(TypedDict):
    username: str
    hashed_password: bytes
    role: str
