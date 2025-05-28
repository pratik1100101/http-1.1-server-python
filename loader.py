import importlib
import json
import os
from database.tables import UserTable
from router import Router
from utils.auth_utils import hash_password


def load_routes(router: Router) -> None:
    # This loads the routes specified in the /config/routes.json file

    routes_config_path = os.path.join("config", "routes.json")

    try:
        with open(routes_config_path, "r") as f:
            config = json.load(f)
    except FileNotFoundError:
        print(f"Error: Routes configuration file not found at {routes_config_path}")
        return
    except json.JSONDecodeError:
        print(
            f"Error: Invalid JSON in routes configuration file at {routes_config_path}"
        )
        return
    except Exception as e:
        print(f"Error: ")  #### NEED TO EDIT THIS #####
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
        "login_handler": None,
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
        handler_map["login_handler"] = auth_handlers_module.login_handler

    except ImportError as i:
        print(f"Error importing handler modules: {i}")
        return
    except Exception as e:
        print(f"Error : {e}")  #### NEED TO EDIT THIS #####
        return

    for route_entry in routes_list:
        method = route_entry.get("method")
        path = route_entry.get("path")
        handler_name = route_entry.get("handler")
        handler_args = route_entry.get("handler_args", {})

        if not all([method, path, handler_name]):
            print(f"Warning: Skipping malformed route entry: {route_entry}")
            continue

        handler = handler_map.get(handler_name)
        if handler is None:
            print(
                f"Warning: Handler '{handler_name}' not found for route {method} {path}. Skipping"
            )
            continue

        router.add_route(method, path, handler, handler_args)

    print(f"Routes loaded from {routes_config_path}")


def load_users(user_table: UserTable):

    users_config_path = os.path.join("config", "users.json")

    if os.path.exists(users_config_path):

        with open(users_config_path, "r") as f:
            users_data = json.load(f)

        for user_info in users_data:
            username = user_info["username"]
            password = user_info["password"]  # This is plaintext from config
            role = user_info["role"]

            # Check if user already exists to avoid re-hashing/adding on every restart
            try:
                got_user = user_table.get_user_by_username(username)
            except ValueError:
                got_user = False

            if not got_user:
                user_table.add_user(username, password, role)
                print(f"Added User: {username}")

        print(f"Users added from {users_config_path}")
    else:
        print(f"Warning: {users_config_path} not found. No initial users loaded.")
