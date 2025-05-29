import json
from typing import Tuple

from psycopg2 import IntegrityError
from database.user_repository import create_user, get_user_by_username
from database.db_config import start_db
from decorators import protected_route
from utils.auth_utils import check_password, create_jwt_token, hash_password
from webserver import Request


def register_user(request: Request) -> Tuple[int, str, bytes]:

    # Check if the request object has all the data you need.
    if request.method != "POST":
        return 405, "text/plain", b"405 Method Not Allowed"
    if not request.decoded_body:
        return 400, "text/plain", b"400 Bad Requesr: Request body is empty."

    try:
        # Here you create the json object from the string so that you can get
        # fast, safe and structured access to the body.
        data = json.loads(request.decoded_body)
        username = data.get("username")
        password = data.get("password")

        # Basic check to ensure that there is no data missing from the body.
        if not username or not password:
            return (
                400,
                "application/json",
                # Ensure you are encoding the json objects to reutrn the correct response format.
                json.dumps({"error": "Username and password are required."}).encode(
                    "utf-8"
                ),
            )

        # The 'with' statement basically lets us acquire some resource, use it, and then release it safely.
        with start_db() as session:

            # In the background what start_db() does is that it sets up the session and waits for the 'with'
            # block to execute before closing the session.

            if get_user_by_username(session, username):
                # The registration fails if the user already exists.
                print(f"Registration failed: User '{username}' already exists.")
                return (
                    409,
                    "application/json",
                    # Ensure you are encoding the json objects to reutrn the correct response format.
                    json.dumps({"error": f"User '{username}' already exists"}).encode(
                        "utf-8"
                    ),
                )

            # We use the functions in the auth_utils and user_repository to get and store the data.
            hashed_password = hash_password(password)
            user = create_user(
                session, username=username, hashed_password=hashed_password, role="user"
            )
            print(f"User '{user.user_id}' registered successfully with ID: {user.id}.")
            return (
                201,
                "application/json",
                # Ensure you are encoding the json objects to reutrn the correct response format.
                json.dumps(
                    {"message": "User registered successfully", "user_id": user.user_id}
                ).encode("utf-8"),
            )

    # Catched any errors during decoding or encoding json objects.
    except json.JSONDecodeError:
        print("Registration failed: Invalid JSON in request body.")
        return 400, "text/plain", b"400 Bad Request: Invalid JSON in request body."
    # Catch database unique constraint violations to ensure integrity.
    except IntegrityError:
        print(
            f"Registration failed: Database integrity error, user_id might be duplicate."
        )
        return (
            409,
            "application/json",
            # Ensure you are encoding the json objects to reutrn the correct response format.
            json.dumps({"error": "Database error: User ID might be duplicate"}).encode(
                "utf-8"
            ),
        )
    # Catches all other exceptions.
    except Exception as e:
        print(f"Error during user registration: {e}")
        return 500, "text/plain", b"500 Internal Server Error: Could not register user."


def login_user(request: Request) -> Tuple[int, str, bytes]:

    # Check if the request object has all the data you need.
    if request.method != "POST":
        return 405, "text/plain", b"405 Method Not Allowed"
    if not request.decoded_body:
        return 400, "text/plain", b"400 Bad Requesr: Request body is empty."

    try:
        # Gets the json object.
        data = json.loads(request.decoded_body)
        username = data.get("username")
        password = data.get("password")

        # Basic check to ensure that there is no data missing from the body.
        if not username or not password:
            return (
                400,
                "application/json",
                # Ensure you are encoding the json objects to reutrn the correct response format.
                json.dumps({"error": "Username and password are required."}).encode(
                    "utf-8"
                ),
            )

        with start_db() as session:
            user = get_user_by_username(session, username)

            # Gives the static type error but this is correct hence we ignore it.
            if user and check_password(password, user.hashed_password):  # type: ignore
                # If user is authenticated, we generate a JWT token using the auth_utils function.
                token_payload = {"username": user.username, "role": user.role}
                jwt_token = create_jwt_token(token_payload)
                print(f"User '{username}' logged in sucessfully.")
                return (
                    200,
                    "application/json",
                    json.dumps(
                        {"message": "Login Sucessful", "token": jwt_token}
                    ).encode("utf-8"),
                )
            else:
                print(f"Login failed: Invalid credentials for user '{username}'.")
                return (
                    401,
                    "application/json",
                    # Ensure you are encoding the json objects to reutrn the correct response format.
                    json.dumps({"error": "Invalid credentials"}).encode("utf-8"),
                )
    # Catched any errors during decoding or encoding json objects.
    except json.JSONDecodeError:
        print("Registration failed: Invalid JSON in request body.")
        return 400, "text/plain", b"400 Bad Request: Invalid JSON in request body."
    # Catches all other exceptions.
    except Exception as e:
        print(f"Error during user registration: {e}")
        return 500, "text/plain", b"500 Internal Server Error: Could not register user."


# Marking this as protected so that access is restricted to loggen in users.
@protected_route
def get_user_profile(request: Request) -> Tuple[int, str, bytes]:

    # Check if the request object has all the data you need.
    if request.method != "GET":
        return 405, "text/plain", b"405 Method Not Allowed"
    if not request.decoded_body:
        return 400, "text/plain", b"400 Bad Requesr: Request body is empty."

    # The auth_middleware would have already populated request.user if the token is valid.
    # Adding this for type safety in the later request.user.get() calls
    if not hasattr(request, "user") or not request.user:
        return 401, "text/plain", b"401 Unauthorized: User data missing."

    # We get the user and role from the jwt token.
    username_from_token = request.user.get("username")
    user_role_from_token = request.user.get("role")
    username_from_db = None
    user_created_at = None

    # We have s stricter check than just 'not username_from_token', since we are dealing with data
    # from sensitive payload (jwt).
    if not isinstance(username_from_token, str):
        print(
            f"Profile access failed: 'user_id' missing or invalid in token payload for user: {username_from_token}"
        )
        return (
            400,
            "application/json",
            # Ensure you are encoding the json objects to reutrn the correct response format.
            json.dumps(
                {"error": "Bad Request: User ID missing or invalid in token payload."}
            ).encode("utf-8"),
        )

    with start_db() as session:
        # Retrives the information about the user requesting data.
        db_user = get_user_by_username(session, username_from_token)
        if db_user:
            username_from_db = db_user.username
            user_created_at = db_user.created_at.isoformat()
        else:
            print(
                f"Profile access failed: User '{username_from_token}' from token not found in database."
            )
            return (
                404,
                "application/json",
                # Ensure you are encoding the json objects to reutrn the correct response format.
                json.dumps({"error": "User not found in database."}).encode("utf-8"),
            )

    # We create a json object that we can serialize to a string when returning in the response.
    profile_data = {
        "message": "User profile data",
        "username_from_token": username_from_token,
        "role_from_token": user_role_from_token,
        "username_from_db": username_from_db,
        "created_at": user_created_at,
    }

    print(f"Profile accessed for user: {username_from_token}")
    # Ensure you are encoding the json objects to reutrn the correct response format.
    return 200, "application/json", json.dumps(profile_data).encode("utf-8")
