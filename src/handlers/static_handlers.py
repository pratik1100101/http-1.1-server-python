import mimetypes
import os
from src.webserver import Request


def _get_content_type(file_path: str) -> str:
    # Add more types if the below mimetypes doesn't cover them well.
    mimetypes.add_type("text/css", ".css")
    mimetypes.add_type("application/javascript", ".js")
    mimetypes.add_type("image/x-icon", ".ico")  # For favicon.ico.
    mimetypes.add_type("image/jpeg", ".jpeg")
    mimetypes.add_type("image/gif", ".gif")

    # .add_type() is a proactive measure to ensure that the web server consistently provides the correct
    # Content-Type header for these specific, commonly used web assets, regardless of any change in the
    # mimetypes database on the system where your server runs.

    # Use .guess_type() function if we can't find the format above.
    # If it can't guess, default to 'application/octet-stream' (binary file).
    content_type, _ = mimetypes.guess_type(file_path)
    return content_type if content_type else "application/octet-stream"


def serve_static_file(request: Request, filepath: str):
    # The request is passed here as an arg but never used. This is intended as the request object will be
    # used by other methods. This gives our framework a consistency in terms of args for all handlers

    web_root_dir = request.web_root_dir
    full_path = os.path.join(web_root_dir, filepath)
    # On Linux/macOS: "webroot/index.html"
    # On Windows: "webroot\\index.html"

    try:
        # We check if the given address exists in the webroot dir
        if not os.path.isfile(full_path):
            print(f"File not found: {full_path}")
            return 404, "text/plain", b"404 Not Found: Static file not found."

        # Always use with when using open() since it will close the file once we are done reading
        with open(full_path, "rb") as f:
            content = f.read()

        # We use the mimetypes library to get the content type and not guess what the file might be
        content_type = _get_content_type(full_path)

        return 200, content_type, content

    # This is a common pattern in error handling in a race condition when building web servers.
    # This is added if the file gets deleted after we process the .isfle() and we don't return is as
    # internal server error but a file not found. Returning the correct status codes is important in HTTP.
    except FileNotFoundError:
        return 404, "text/plain", b"404 Not Found: Static file not found."
    except Exception as e:
        # Catch any other error we get while we are reading the file or getting the content_type
        print(f"Error serving static file {filepath}: {e}")
        return (
            500,
            "text/plain",
            f"500 Internal Server Error: Could not serve file ({e}).".encode("utf-8"),
        )
