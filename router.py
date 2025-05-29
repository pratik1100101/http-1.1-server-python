from typing import Any, Callable, Dict, Optional, Tuple


class Router:
    # The router's main job is to act like a traffic controller. When a request arrives with a path and method,
    # the router inspects this, and then decides which specific piece of code (called a "handler") should process
    # that request.

    def __init__(self) -> None:
        # Routes are stored as:
        # self.routes = {
        #                "METHOD": {
        #                           "path": {"handler": handler,"handler_args": handler_args,},},}
        self.routes = {}

    def add_route(
        self,
        method: str,
        path: str,
        handler: Callable,
        handler_args: Optional[Dict[str, Any]] = None,
    ) -> None:

        # Always process the HTTP methods with .upper() to ensure consistency
        method = method.upper()

        if method not in self.routes:
            # Adds a method to the route dictionary if it doesn't exist
            self.routes[method] = {}

        # Finally we create the handler and its arguments for the specific path and method
        self.routes[method][path] = {
            "handler": handler,
            "handler_args": handler_args,
        }
        print(f"Route added: {method} {path}")

    # This method is used by the server to get the handler and its args.
    def get_handler(
        self, method: str, path: str
    ) -> Optional[Tuple[Optional[Callable], Optional[Dict[str, Any]]]]:

        route_info = self.routes.get(method, {}).get(path)

        if route_info:
            return route_info["handler"], route_info["handler_args"]
        return None, None

    # This method is used by the auth_middleware to check protection status
    def get_route_info(self, method: str, path: str) -> Optional[Dict[str, Any]]:
        return self.routes.get(method, {}).get(path)
