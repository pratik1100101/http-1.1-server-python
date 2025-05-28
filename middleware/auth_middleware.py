import os
from typing import Any, Callable, Tuple
from dotenv import load_dotenv
import jwt

from webserver import Request

load_dotenv(dotenv_path="../.env")
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "")
ALGORITHM = os.getenv("ALGORITHM", "HS256")


def auth_middleware(next_handler: Callable) -> Callable:

    # Check if the next_handler is marked as a protected route.
    # If not, simply pass the request through without authentication.
    if not getattr(next_handler, "_is_protected", False):
        return next_handler

    def wrapper(request: Request, **handler_args: Any) -> Tuple[int, str, bytes]:
        # Gets the data stored in the Authorization header
        auth_header = request.headers.get("Authorization")

        # If the request has no auth then fails instantly
        if not auth_header:
            print("Authentication failed: No Authorization header.")
            return 401, "text/plain", b"401 Unauthorized: Authorization header missing."

        # Expecting format: "Bearer <token>"
        parts = auth_header.split(" ")

        # Check if the auth headered is correctly formatted
        if len(parts) != 2 or parts[0].lower() != "bearer":
            print("Authentication failed: Malformed Authorization header.")
            return (
                401,
                "text/plain",
                b"401 Unauthorized: Malformed Authorization header.",
            )

        # Extract the token from the header
        token = parts[1]

        try:
            decoded_payload = jwt.decode(token, SECRET_KEY, ALGORITHM)

            request.user = decoded_payload
            print(f"Authentication successful for user: {request.user.get('user_id')}")

            return next_handler(request, **handler_args)

        except jwt.ExpiredSignatureError:
            print("Authentication failed: JWT has expired.")
            return 401, "text/plain", b"401 Unauthorized: Token has expired."
        except jwt.InvalidTokenError:
            print("Authentication failed: Invalid JWT.")
            return 401, "text/plain", b"401 Unauthorized: Invalid token."
        except Exception as e:
            # Catch any other unexpected errors during JWT processing
            print(f"Authentication failed: An unexpected error occurred: {e}")
            return (
                500,
                "text/plain",
                b"500 Internal Server Error: Authentication error.",
            )

    return wrapper
