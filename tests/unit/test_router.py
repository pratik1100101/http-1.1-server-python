import pytest
from src.router import Router


# Define simple handler functions for testing
def handler_one():
    return "Handler One Executed"


def handler_two(name):
    return f"Handler Two Executed for {name}"


def handler_three(item_id, category):
    return f"Handler Three Executed for {item_id} in {category}"


class TestRouter:

    # Provides a fresh Router instance for each test.
    @pytest.fixture
    def router(self):
        return Router()

    #### ADD_ROUTE() TESTS ####
    # Test basic route registration for different methods and paths.
    def test_add_route_basic(self, router):
        router.add_route("GET", "/home", handler_one)
        router.add_route("POST", "/submit", handler_two)
        router.add_route("PUT", "/update/123", handler_three)

        assert router.get_handler("GET", "/home") == (handler_one, None)
        assert router.get_handler("POST", "/submit") == (handler_two, None)
        assert router.get_handler("PUT", "/update/123") == (handler_three, None)
        assert router.get_route_info("GET", "/home") == {
            "handler": handler_one,
            "handler_args": None,
        }

    # Test route registration with handler arguments.
    def test_add_route_with_handler_args(self, router):
        args_one = {"name": "Alice"}
        router.add_route("GET", "/users/alice", handler_two, args_one)

        handler, args = router.get_handler("GET", "/users/alice")
        assert handler == handler_two
        assert args == args_one

        route_info = router.get_route_info("GET", "/users/alice")
        assert route_info["handler"] == handler_two
        assert route_info["handler_args"] == args_one

    # Test that HTTP methods are treated case-insensitively.
    def test_add_route_case_insensitivity_method(self, router):
        router.add_route("get", "/products", handler_one)
        router.add_route("pOsT", "/data", handler_two)

        assert router.get_handler("GET", "/products") == (handler_one, None)
        assert router.get_handler("post", "/data") == (handler_two, None)

    # Test that adding a duplicate route overwrites the previous one.
    def test_add_route_duplicate_overwrite(self, router):
        router.add_route("GET", "/test", handler_one)
        assert router.get_handler("GET", "/test") == (handler_one, None)

        # Add a new handler for the same method and path
        router.add_route("GET", "/test", handler_two)
        assert router.get_handler("GET", "/test") == (handler_two, None)

        # Add a new handler and args for the same method and path
        new_args = {"key": "value"}
        router.add_route("GET", "/test", handler_three, new_args)
        assert router.get_handler("GET", "/test") == (handler_three, new_args)

    #### GET_HANDLER() TESTS ####
    # Test getting handler for a path that does not exist.
    def test_get_handler_non_existent_path(self, router):
        router.add_route("GET", "/existing", handler_one)
        handler, args = router.get_handler("GET", "/nonexistent")
        assert handler is None
        assert args is None

    # Test getting handler for a method that does not exist for a path.
    def test_get_handler_non_existent_method(self, router):
        router.add_route("GET", "/api", handler_one)
        handler, args = router.get_handler("POST", "/api")
        assert handler is None
        assert args is None

    # Test getting handler from an empty router.
    def test_get_handler_empty_router(self, router):
        handler, args = router.get_handler("GET", "/anything")
        assert handler is None
        assert args is None

    #### GET_ROUTE_INFO() TESTS ####
    # Test getting route info for a non-existent route.
    def test_get_route_info_non_existent_route(self, router):
        router.add_route("GET", "/home", handler_one)
        assert router.get_route_info("POST", "/home") is None
        assert router.get_route_info("GET", "/nonexistent") is None

    # Test that get_route_info handles case-insensitive methods.
    def test_get_route_info_case_insensitivity_method(self, router):
        router.add_route("GET", "/status", handler_one)
        assert router.get_route_info("get", "/status") == {
            "handler": handler_one,
            "handler_args": None,
        }
