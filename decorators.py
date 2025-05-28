from typing import Callable, Any


def protected_route(handler: Callable) -> Callable:
    # Marks routes as protected which the auth_middleware will check for this attribute.

    handler._is_protected = True  # Custom attribute to signal protection
    return handler
