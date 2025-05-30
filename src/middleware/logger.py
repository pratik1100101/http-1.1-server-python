import datetime
import time
from typing import Any, Callable, Dict, Tuple
from src.webserver import Request


def logger_middleware(handler_function: Callable) -> Callable:
    # Don't confuse the scattered print statements and this logger, the scattered print statements
    # are for learning and debugging purposes, but the logger is made for:
    # Monitoring, understanding operational behavior and performance of the server.

    def wrapper(
        request: Request, **handler_args: Dict[str, Any]
    ) -> Tuple[int, str, bytes]:

        # Get the time the request was.
        start_time = time.time()
        # Not dealing with time conversions here for simplicity.
        timestamp = datetime.datetime.now().strftime("%Y-%m-%D %H:%M:%S")
        print(f"[{timestamp}] Incoming Request: {request.method} {request.path}")

        try:
            status_code, content_type, content_bytes = handler_function(
                request, **handler_args
            )
            end_time = time.time()
            duration = (end_time - start_time) * 1000
            print(
                f"[{timestamp}] Outgoing Response: {request.method} {request.path} - Status: {status_code} - Duration: {duration:.2f}ms"
            )

            return status_code, content_type, content_bytes
        except Exception as e:
            # If an error occurs in the handler_function or a subsequent middleware we log it.
            end_time = time.time()
            duration = (end_time - start_time) * 1000
            print(
                f"[{timestamp}] Error during handling {request.method} {request.path}: {e} - Duration: {duration:.2f}ms"
            )
            # Re-raise the exception or handle it to ensure webserver.py's try-except catches it
            raise

    # IMPORTANT: The logger_middleware RETURNS the wrapper function itself.
    # It does NOT call wrapper here
    return wrapper
