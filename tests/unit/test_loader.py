import importlib
import pytest
import json
import os
from src.router import Router
from src.loader import load_routes, bind_handler


# Mock handler functions for testing purposes
def mock_serve_static_file(request):
    return "static_file"


def mock_get_data(request, user_id=None):
    return f"data_for_{user_id}"


def mock_post_data(request, payload):
    return f"posted_{payload}"


def mock_register_user(request):
    return "user_registered"


def mock_login_user(request, username, password):
    return f"logged_in_{username}"


def mock_get_user_profile(request, profile_id):
    return f"profile_{profile_id}"


class TestLoader:

    # Provides a fresh Router instance for each test.
    @pytest.fixture
    def router_instance(self):
        return Router()

    # Mocks the handler modules and their functions using mocker.
    @pytest.fixture
    def mock_handlers_modules(self, mocker):
        # Store the original import_module function
        original_import_module = importlib.import_module

        # Mock all the handlers in src.handlers to the functions we defined above.
        # This allows us to see if the functions are assigned correctly without ever calling them.
        mock_static_handlers = mocker.Mock()
        mock_static_handlers.serve_static_file = mock_serve_static_file

        mock_api_handlers = mocker.Mock()
        mock_api_handlers.get_data = mock_get_data
        mock_api_handlers.post_data = mock_post_data

        mock_auth_handlers = mocker.Mock()
        mock_auth_handlers.register_user = mock_register_user
        mock_auth_handlers.login_user = mock_login_user
        mock_auth_handlers.get_user_profile = mock_get_user_profile

        # Not using lambda function for simplicity.
        def mock_import_module(module_name):
            # Return mocked modules for our handlers
            handler_modules = {
                "src.handlers.static_handlers": mock_static_handlers,
                "src.handlers.api_handlers": mock_api_handlers,
                "src.handlers.auth_handlers": mock_auth_handlers,
            }

            if module_name in handler_modules:
                return handler_modules[module_name]
            else:
                # For any other module, use the original import_module
                return original_import_module(module_name)

        # Patch with the safer side_effect
        mocker.patch("importlib.import_module", side_effect=mock_import_module)
        # We don't actually require yield here since mocker cleans up (tears down) after it is done.
        # But I am keeping this here for clarity and intent.
        yield

    #### LOAD_ROUTES() TESTS ####
    # Test loading a valid routes.json file and ensures routes are registered.
    def test_load_routes_valid_config(
        self, mocker, router_instance, mock_handlers_modules
    ):
        mock_routes_config = {
            "routes": [
                {
                    "method": "GET",
                    "path": "/",
                    "handler": "serve_static_file",
                },
                {
                    "method": "GET",
                    "path": "/api/data",
                    "handler": "get_data",
                    "handler_args": {"user_id": 123},
                },
                {
                    "method": "POST",
                    "path": "/api/data",
                    "handler": "post_data",
                    "handler_args": {"payload": "test"},
                },
                {
                    "method": "POST",
                    "path": "/register",
                    "handler": "register_user",
                },
                {
                    "method": "POST",
                    "path": "/login",
                    "handler": "login_user",
                    "handler_args": ["testuser", "testpass"],
                },
                {
                    "method": "GET",
                    "path": "/profile/<username>",
                    "handler": "get_user_profile",
                    "handler_args": {"username": "testuser"},
                },
            ]
        }

        # Mock builtins.open using mocker.patch.
        # This automatically handles closing and cleanup so no need for with here.
        mock_open = mocker.patch(
            "builtins.open",
            mocker.mock_open(read_data=json.dumps(mock_routes_config)),
        )
        with open("dummy_path.json", "r") as f:
            content = f.read()

        # Assert that the file was open correctly and content accessed was same.
        mock_open.assert_called_once_with("dummy_path.json", "r")
        assert content == json.dumps(mock_routes_config)

        # Mock builtins.print to suppress output during tests.
        mocker.patch("builtins.print")

        load_routes(router_instance)

        # Verify that routes are added to the router.
        handler, args = router_instance.get_handler("GET", "/")
        assert handler is not None and callable(handler)

        # For handlers with no original args, the bound handler should be the original.
        # Hence we are checking that the bound function is stored as itself without any args.
        assert router_instance.get_handler("GET", "/")[0] is mock_serve_static_file

        # For handlers with args, the bound handler is a new callable with its args in place.
        bound_handler_get_data, _ = router_instance.get_handler("GET", "/api/data")
        assert callable(bound_handler_get_data)
        # Test the handler's behavior by providing a mock request object since we passed:
        # "user_id": 123 as an argument above so it should return f"data_for_{user_id}".
        assert bound_handler_get_data(mocker.Mock()) == "data_for_123"

        bound_handler_post_data, _ = router_instance.get_handler("POST", "/api/data")
        assert callable(bound_handler_post_data)
        assert bound_handler_post_data(mocker.Mock()) == "posted_test"

        bound_handler_login_user, _ = router_instance.get_handler("POST", "/login")
        assert callable(bound_handler_login_user)
        assert bound_handler_login_user(mocker.Mock()) == "logged_in_testuser"

        # Check if all added routes are present and added correctly.
        assert router_instance.get_handler("POST", "/register")[0] is not None
        assert router_instance.get_handler("GET", "/profile/<username>")[0] is not None

    # Test handling of a missing routes.json file.
    def test_load_routes_missing_file(self, mocker, router_instance):
        # Simulating the absence of a file by giving the open() an error directly.
        mocker.patch("builtins.open", side_effect=FileNotFoundError)
        mock_print = mocker.patch("builtins.print")

        load_routes(router_instance)
        mock_print.assert_called_once_with(
            f"Error: Routes configuration file not found at {os.path.join('config', 'routes.json')}"
        )
        # Ensure no routes were added since we did not find the file.
        assert not router_instance.routes

    # Test handling of malformed JSON in routes.json.
    def test_load_routes_malformed_json(self, mocker, router_instance):
        # Simulate open() getting a file and reading the data as a malformed json obj.
        mocker.patch(
            "builtins.open", mocker.mock_open(read_data='{"routes": [not valid json}')
        )
        mock_print = mocker.patch("builtins.print")

        # Since the opened data above will be accessed by json.load() we will get an JSONDecodeError.
        load_routes(router_instance)
        mock_print.assert_called_once_with(
            f"Error: Invalid JSON in routes configuration file at {os.path.join('config', 'routes.json')}"
        )
        assert not router_instance.routes

    # Test handling of config without 'routes' key.
    def test_load_routes_invalid_config_structure_no_routes_key(
        self, mocker, router_instance, mock_handlers_modules
    ):
        mock_routes_config = {"other_key": []}
        mocker.patch(
            "builtins.open", mocker.mock_open(read_data=json.dumps(mock_routes_config))
        )
        mock_print = mocker.patch("builtins.print")

        load_routes(router_instance)

        # Assert that the error was caught and no routes were added.
        mock_print.assert_any_call(
            f"Error: Missing 'routes' key in routes configuration file at {os.path.join('config', 'routes.json')}"
        )
        assert not router_instance.routes

    # Test handling of config where 'routes' is not a list.
    def test_load_routes_invalid_config_structure_routes_not_list(
        self, mocker, router_instance, mock_handlers_modules
    ):
        mock_routes_config = {"routes": "not_a_list"}
        mocker.patch(
            "builtins.open", mocker.mock_open(read_data=json.dumps(mock_routes_config))
        )
        mock_print = mocker.patch("builtins.print")

        load_routes(router_instance)
        mock_print.assert_called_once_with("Error: 'routes' key in config must be list")
        assert not router_instance.routes

    # Test handling of a route entry with a handler that doesn't exist in modules.
    def test_load_routes_missing_handler_function(self, mocker, router_instance):
        mock_routes_config = {
            "routes": [
                {"method": "GET", "path": "/missing", "handler": "non_existent_handler"}
            ]
        }
        mocker.patch(
            "builtins.open", mocker.mock_open(read_data=json.dumps(mock_routes_config))
        )
        mock_print = mocker.patch("builtins.print")

        # We mock importlib.import_module again instead of using mock_handlers_modules.
        # This is to ensure 'non_existent_handler' isn't available
        mocker.patch(
            "importlib.import_module",
            side_effect=lambda module_name: {
                "src.handlers.static_handlers": mocker.Mock(
                    serve_static_file=mock_serve_static_file
                ),
                "src.handlers.api_handlers": mocker.Mock(get_data=mock_get_data),
                "src.handlers.auth_handlers": mocker.Mock(login_user=mock_login_user),
            }.get(module_name, mocker.Mock()),
        )

        load_routes(router_instance)
        # Since the handler will not exist it will never be added and loader will skip it.
        mock_print.assert_any_call(
            "Warning: Handler 'non_existent_handler' not found for route GET /missing. Skipping"
        )
        assert not router_instance.get_handler("GET", "/missing")[0]

    # Test handling of malformed route entries (missing method, path, or handler).
    def test_load_routes_missing_required_fields(
        self, mocker, router_instance, mock_handlers_modules
    ):
        mock_routes_config = {
            "routes": [
                {"path": "/no-method", "handler": "serve_static_file"},
                {"method": "GET", "handler": "serve_static_file"},
                {"method": "POST", "path": "/no-handler"},
            ]
        }
        mocker.patch(
            "builtins.open", mocker.mock_open(read_data=json.dumps(mock_routes_config))
        )
        mock_print = mocker.patch("builtins.print")

        load_routes(router_instance)
        # Adding these routes should be skipped since they are not in the correct format.
        mock_print.assert_any_call(
            "Warning: Skipping malformed route entry: {'path': '/no-method', 'handler': 'serve_static_file'}"
        )
        mock_print.assert_any_call(
            "Warning: Skipping malformed route entry: {'method': 'GET', 'handler': 'serve_static_file'}"
        )
        mock_print.assert_any_call(
            "Warning: Skipping malformed route entry: {'method': 'POST', 'path': '/no-handler'}"
        )
        # Checking that no routes should be added.
        assert not router_instance.routes

    #### BIND_HANDLER() TESTS ####
    # Test bind_handler when no handler_args are provided.
    def test_bind_handler_no_args(self, mocker):

        def original_handler(req):
            return "no_args"

        bound = bind_handler(original_handler, None)
        assert bound is original_handler
        assert bound(mocker.Mock()) == "no_args"

    # Test bind_handler with dictionary handler_args.
    def test_bind_handler_dict_args(self, mocker):

        def original_handler(req, param1, param2):
            return f"dict_args_{param1}_{param2}"

        # Here we define the params as a dict for the handler to bind them to the handler.
        args = {"param1": "value1", "param2": "value2"}
        bound = bind_handler(original_handler, args)
        assert callable(bound)
        assert bound(mocker.Mock()) == "dict_args_value1_value2"

    # Test bind_handler with list handler_args.
    def test_bind_handler_list_args(self, mocker):

        def original_handler(req, param1, param2):
            return f"list_args_{param1}_{param2}"

        # Here we define the params as a list for the handler to bind them to the handler.
        args = ["valueA", "valueB"]
        bound = bind_handler(original_handler, args)
        assert callable(bound)
        assert bound(mocker.Mock()) == "list_args_valueA_valueB"

    # Test bind_handler with a single, non-list/dict argument.
    def test_bind_handler_single_arg(self, mocker):

        def original_handler(req, param):
            return f"single_arg_{param}"

        # Finally checking if a single arg can be bounded to a handler.
        arg = "single_value"
        bound = bind_handler(original_handler, arg)
        assert callable(bound)
        assert bound(mocker.Mock()) == "single_arg_single_value"
