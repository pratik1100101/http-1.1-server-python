import functools
import importlib
import json
import os
from router import Router


def load_routes(router: Router) -> None:
    # This loads the routes specified in the /config/routes.json file

    routes_config_path = os.path.join("config", "routes.json")

    try:
        with open(routes_config_path, "r") as f:
            config = json.load(f)
    # Catches errors if there is no file.
    except FileNotFoundError:
        print(f"Error: Routes configuration file not found at {routes_config_path}")
        return
    # Catches specific error info while decoding json file.
    except json.JSONDecodeError:
        print(
            f"Error: Invalid JSON in routes configuration file at {routes_config_path}"
        )
        return
    # Catch any other unexpected errors during file reading.
    except Exception as e:
        print(f"Error: 'routes' key in config must be a list.")
        return

    routes_list = config.get("routes", [])
    if not isinstance(routes_list, list):
        print(f"Error: 'routes' key  in config must be list")
        return

    # Define a mapping from handler name so that we can map it to the actual function.
    # This avoids dynamic imports by string which can be easy to go wrong with,
    # and it explicitly declares which handlers are expected.
    handler_map = {
        "serve_static_file": None,
        "get_data": None,
        "post_data": None,
        "register_user": None,
        "login_user": None,
        "get_user_profile": None,
    }

    # We will look up the handlers by importing their module.
    # This allows us to list handler functions by name in the config.
    try:
        static_handlers_module = importlib.import_module("handlers.static_handlers")
        handler_map["serve_static_file"] = static_handlers_module.serve_static_file

        api_handlers_module = importlib.import_module("handlers.api_handlers")
        handler_map["get_data"] = api_handlers_module.get_data
        handler_map["post_data"] = api_handlers_module.post_data

        auth_handlers_module = importlib.import_module("handlers.auth_handlers")
        handler_map["register_user"] = auth_handlers_module.register_user
        handler_map["login_user"] = auth_handlers_module.login_user
        handler_map["get_user_profile"] = auth_handlers_module.get_user_profile

    # Catches a specific error when importing handlers.
    except ImportError as e:
        print(f"Error importing handler modules: {e}")
        return
    # Catches if a handler function is missing in a module.
    except AttributeError as e:
        print(f"Error finding handler function in module: {e}")
        return
    # Catches any other unexpected errors during handler loading.
    except Exception as e:
        print(f"An unexpected error occurred during handler loading: {e}")
        return

    # Loop through all the routes in the config file to add them to the router.
    for route_entry in routes_list:
        method = route_entry.get("method")
        path = route_entry.get("path")
        handler_name = route_entry.get("handler")
        handler_args = route_entry.get("handler_args")
        protected = route_entry.get("protected", False)

        # Ensures that we have the basic arguments that we need if a route is called.
        if not all([method, path, handler_name]):
            print(f"Warning: Skipping malformed route entry: {route_entry}")
            continue

        # Ensures that the handler_name is correct and is in the handler_map defined above.
        handler = handler_map.get(handler_name)
        if handler is None:
            print(
                f"Warning: Handler '{handler_name}' not found for route {method} {path}. Skipping"
            )
            continue

        # Here we are binding the arguments of the handler to itself by making it a Tuple
        bound_handler = handler
        # Checks if args is None or if it is anything else and binds it to the handler
        if handler_args is not None:
            # functools.partial() assigns the arguments to the handler function directly but doesn't call it.
            if isinstance(handler_args, list):
                bound_handler = functools.partial(handler, *handler_args)
            elif isinstance(handler_args, dict):
                bound_handler = functools.partial(handler, **handler_args)
            else:
                bound_handler = functools.partial(handler, handler_args)

        router.add_route(method, path, bound_handler, protected=protected)

    print(f"Routes loaded from {routes_config_path}")
