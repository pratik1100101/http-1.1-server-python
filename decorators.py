from typing import Any, Callable, cast


def protected_route(handler: Callable) -> Callable:
    # Marks routes as protected which the auth_middleware will check for this attribute.

    # Using cast here since Pylance is being a pain in the bottom with type check.
    # We are adding a custom attribute to mark the function as protected for auth.
    cast(Any, handler)._is_protected = True
    return handler
