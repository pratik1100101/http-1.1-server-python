from datetime import datetime, timedelta, timezone
import os
from typing import Optional
import bcrypt
from dotenv import load_dotenv
import jwt

load_dotenv(dotenv_path="../.env")
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))


def hash_password(password: str) -> str:
    # Function to securely hash passwords using `bcrypt` with some added salt.
    hashed_password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    return hashed_password.decode("utf-8")


def check_password(password: str, hashed_password: str) -> bool:
    # Function to verify a plaintext password against a hashed one.
    return bcrypt.checkpw(password.encode("utf-8"), hashed_password.encode("utf-8"))


def create_jwt_token(payload: dict) -> str:
    # Function to generate a JWT from a given payload (e.g., `username`, `role`, `expiration_time`).
    to_encode = payload.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc)})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_jwt_token(token: str) -> Optional[dict]:
    # Function to validate an incoming JWT and return its decoded payload if valid, or `None` otherwise.

    try:
        decoded_payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return decoded_payload
    except jwt.ExpiredSignatureError:
        print("Token has expired.")
        return None
    except jwt.InvalidTokenError:
        print("Invalid token.")
        return None
    except Exception as e:
        print(f"An unexpected error occurred during token verification: {e}")
        return None
