import json
from typing import Tuple
from utils.auth_utils import check_password, create_jwt_token
from webserver import Request

# Important, it ensures we will only have one instance of UserTable
from database.db import user_table


def login_handler(request: Request) -> Tuple[int, str, bytes]:

    if request.method != "POST":
        return 405, "text/plain", b"405 Method Not Allowed"

    if not request.body:
        return 400, "text/plain", b"400 Bad Request: Request body missing."

    try:
        # Attempt to decode the body as UTF-8 and then parse as JSON
        request_data = json.loads(request.body.decode("utf-8"))

        username = request_data.get("username", "")
        password = request_data.get("password", "")

        if not username or not password:
            return (
                400,
                "text/plain",
                b"400 Bad Request: Username and password are required.",
            )

        # Retrieve user from the in-memory table
        user = user_table.get_user_by_username(username)

        if user and check_password(password, user["hashed_password"]):
            token_payload = {"user_id": user["username"], "role": user["role"]}
            jwt_token = create_jwt_token(token_payload)

            response_data = {"access_token": jwt_token, "token_type": "bearer"}

            return (
                200,
                "application/json",
                json.dumps(response_data).encode("utf-8"),
            )
        else:
            # Invalid credentials
            return 401, "text/plain", b"401 Unauthorized: Invalid credentials."

    except json.JSONDecodeError:
        # Handle cases where the request body is not valid JSON
        return 400, "text/plain", b"400 Bad Request: Invalid JSON in request body."
    except UnicodeDecodeError:
        # Handle cases where the request body cannot be decoded as UTF-8
        return 400, "text/plain", b"400 Bad Request: Could not decode request body."
    except Exception as e:
        # Catch any other unexpected errors during login processing
        print(f"Error in login_handler: {e}")
        return 500, "text/plain", f"500 Internal Server Error: {e}".encode("utf-8")
