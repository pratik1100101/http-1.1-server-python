from typing import Optional, Tuple
from decorators import protected_route
from webserver import Request
import json


def json_response(
    status_code: int, data: dict, headers: Optional[dict] = None
) -> Tuple[int, str, bytes]:
    # Util to create json responses

    # Initialize an empty dict if no custom headers are provided
    # headers is provided here so that we can handle any customer headers later
    if headers is None:
        headers = {}

    try:
        response_body = json.dumps(data).encode("utf-8")
        content_type = "application/json"
        return status_code, content_type, response_body
    except json.JSONDecodeError:
        return 500, "text/plain", b"500 Internal Server Error: JSON encoding failed."
    except Exception as e:
        return (
            500,
            "text/plain",
            f"500 Internal Server Error: {e}.".encode("utf-8"),
        )


@protected_route
def get_data(request: Request) -> Tuple[int, str, bytes]:
    # Handler for GET /api/data. Returns some sample JSON data.
    try:
        print(f"Handling GET request for /api/data. Request headers: {request.headers}")

        user_info = (
            request.user
            if request.user
            else {"message": "No user info (shouldn't happen on protected route)"}
        )
        print(f"Authenticated user for /api/data: {user_info}")

        sample_data = {
            "message": "Hello from Protected API!",
            "method": request.method,
            "path": request.path,
            "authenticated_user": user_info,
        }
        return json_response(200, sample_data)

    except Exception as e:
        # Catch any unexpected errors during data processing
        return 500, "text/plain", f"500 Internal Server Error: {e}".encode("utf-8")


@protected_route
def post_data(request: Request):
    # Handler for POST /api/data. Processes incoming JSON data.

    print(f"Handling POST request for /api/data. Request body: {request.body}")
    if request.body:
        try:
            user_info = (
                request.user
                if request.user
                else {"message": "No user info (shouldn't happen on protected route)"}
            )
            print(f"Authenticated user performing POST: {user_info}")

            received_data = json.loads(request.body.decode("utf-8"))
            response_message = f"Received data from {user_info.get('user_id', 'unknown')}: {received_data}"
            return json_response(
                200,
                {
                    "status": "success",
                    "message": response_message,
                    "received_by_user": user_info.get("user_id"),
                },
            )
        except json.JSONDecodeError:
            return 400, "text/plain", b"400 Bad Request: Invalid JSON in request body."
        except UnicodeDecodeError:
            return 400, "text/plain", b"400 Bad Request: Could not decode request body."
        except Exception as e:
            # Catch any unexpected errors during data processing
            return 500, "text/plain", f"500 Internal Server Error: {e}".encode("utf-8")
    else:
        return 400, "text/plain", b"400 Bad Request: No data received in request body."
