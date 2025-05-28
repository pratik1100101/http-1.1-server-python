from webserver import Request
import json


def get_data(request: Request):
    # Handler for GET /api/data. Returns some sample JSON data.

    print(f"Handling GET request for /api/data. Request headers: {request.headers}")
    sample_data = {
        "message": "Hello from API!",
        "method": request.method,
        "path": request.path,
    }
    return 200, "application/json", json.dumps(sample_data).encode("utf-8")


def post_data(request: Request):
    # Handler for POST /api/data. Processes incoming JSON data.

    print(f"Handling POST request for /api/data. Request body: {request.decoded_body}")
    if request.decoded_body:
        try:
            received_data = json.loads(request.decoded_body)
            response_message = f"Received data: {received_data}"
            return (
                200,
                "application/json",
                json.dumps({"status": "success", "message": response_message}).encode(
                    "utf-8"
                ),
            )
        except json.JSONDecodeError:
            return 400, "text/plain", b"400 Bad Request: Invalid JSON in request body."
    else:
        return 400, "text/plain", b"400 Bad Request: No data received in request body."
