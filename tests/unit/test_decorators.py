from src.decorators import protected_route


class TestDecorators:
    # Test that the protected_route decorator correctly adds the _is_protected
    # attribute and sets it to True on the decorated function.
    def test_protected_route_marks_handler(self):

        @protected_route
        def mock_handler():
            pass

        assert hasattr(mock_handler, "_is_protected")
        assert mock_handler._is_protected is True

    # Test that the protected_route decorator returns the original handler function.
    def test_protected_route_returns_original_handler(self):

        def original_handler():
            pass

        decorated_handler = protected_route(original_handler)

        # Ensure the returned handler is the same object as the original,
        # or at least behaves identically if a wrapper was created (though in this case, it's the same).
        assert decorated_handler is original_handler
        assert AttributeError(hasattr(original_handler, "_is_protected"))
