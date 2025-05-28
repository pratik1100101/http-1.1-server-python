from typing import Any, Callable, Dict, Optional, Tuple


class Router:
    # The router's main job is to act like a traffic controller. When a request arrives with a path and method,
    # the router inspects this, and then decides which specific piece of code (called a "handler") should process
    # that request.

    def __init__(self) -> None:
        # Routes are stored as:
        # self.routes = {
        #                "METHOD": {
        #                           "path": (handler_function, handler_args),},}
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
        self.routes[method][path] = (
            handler,
            handler_args if handler_args is not None else {},
        )
        print(f"Route added: {method} {path}")

    def resolve_route(
        self, method: str, path: str
    ) -> Optional[Tuple[Callable, Dict[str, Any]]]:

        # The WebServer will call this method to check which handler to use

        # Always process the HTTP methods with .upper() to ensure consistency
        method = method.upper()

        # A simple check if there is a handler for the incoming request with a spefcific method and path
        if method in self.routes:
            if path in self.routes[method]:
                print(f"Route resolved: {method} {path}")
                return self.routes[method][path]
        print(f"No route found for: {method} {path}")
        return None


# If you don't want to implement the configuration file approach to routing you can use programmatic
# routing approach below. I wanted to learn both ways hence I implemented both.
####def route(self, method: str, path: str, **decorator_handler_args: Any) -> Callable:
######### I wanted to implement the decorator way of implementing the routes though a decorator
######### like we do in a flask app (@router.route('/', methods=['GET', 'POST'])), but have changed
######### the order of the args to @router.route(methods, path) for consistency in the app

########def decorator(handler: Callable) -> Callable:
############# When the decorator is applied, this inner function gets the handler.
############# We then call the add_route method to register it.

############self.add_route(method, path, handler, decorator_handler_args)

############# We return the original handler
############return handler

########return decorator
