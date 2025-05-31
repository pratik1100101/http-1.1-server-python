import pytest
import json
import logging
from src.webserver import Request
from src.handlers.api_handlers import json_response, get_data, post_data


class TestApiHandlers:
    # Fixture to create a mock Request object using mocker.
    @pytest.fixture
    def mock_request(self, mocker):
        mock_req = mocker.Mock(spec=Request)
        mock_req.method = "GET"
        mock_req.path = "/api/data"
        mock_req.headers = {}
        mock_req.body = b""
        mock_req.user = None
        return mock_req

    # Fixture to mock the @protected_route decorator.
    # The 'autouse=True' makes this fixture run automatically for all tests in this file.
    @pytest.fixture(autouse=True)
    def mock_protected_route_decorator(self, mocker):

        def no_op_decorator(func):
            return func

        mocker.patch(
            "src.handlers.api_handlers.protected_route", side_effect=no_op_decorator
        )

    #### JSON_RESPONSE() TESTS ####
    # Test json_response with basic dictionary data.
    def test_json_response_basic(self):
        status, content_type, body = json_response(200, {"key": "value"})
        assert status == 200
        assert content_type == "application/json"
        assert json.loads(body.decode("utf-8")) == {"key": "value"}

    # Test json_response's error handling while encoding.
    def test_json_response_encoding_failure(self):

        # Create an object that cannot be JSON serialized
        class NonSerializable:
            pass

        status, content_type, body = json_response(200, {"bad_data": NonSerializable()})
        assert status == 500
        assert content_type == "text/plain"
        assert (
            b"500 Internal Server Error: Object of type NonSerializable is not JSON serializable."
            in body
        )

    # Test json_response's error handling for a general exception during encoding.
    def test_json_response_general_exception(self, mocker):

        mocker.patch("json.dumps", side_effect=Exception("Test Error"))
        status, content_type, body = json_response(200, {"key": "value"})
        assert status == 500
        assert content_type == "text/plain"
        assert b"500 Internal Server Error: Test Error." in body

    #### GET_DATA TESTS ####
    # Test get_data with an authenticated user.
    def test_get_data_success_authenticated_user(self, mock_request, caplog):

        mock_request.user = {"username": "testuser", "id": 123}
        mock_request.method = "GET"
        mock_request.path = "/api/data"

        with caplog.at_level(logging.INFO):
            status, content_type, body = get_data(mock_request)

        assert status == 200
        assert content_type == "application/json"
        response_data = json.loads(body.decode("utf-8"))
        assert response_data["message"] == "Hello from Protected API!"
        assert response_data["method"] == "GET"
        assert response_data["path"] == "/api/data"
        assert response_data["authenticated_user"] == {
            "username": "testuser",
            "id": 123,
        }

    # Test get_data when no user info is available (even on a protected route).
    def test_get_data_success_no_user(self, mock_request, caplog):

        # While protected_route should prevent this in a real app, the handler should still function gracefully.
        # Authentication should be handled by auth_middleware.
        mock_request.user = None  # Explicitly set no user
        mock_request.method = "GET"
        mock_request.path = "/api/data"

        with caplog.at_level(logging.INFO):
            status, content_type, body = get_data(mock_request)

        assert status == 200
        assert content_type == "application/json"
        response_data = json.loads(body.decode("utf-8"))
        assert response_data["authenticated_user"] == {
            "message": "No user info (shouldn't happen on protected route)"
        }

    # Test get_data's error handling for unexpected exceptions.
    def test_get_data_exception_handling(self, mock_request, mocker):
        # Simulate an error during data processing by mocking a property
        mocker.patch.object(
            mock_request,
            "method",
            new_callable=mocker.PropertyMock,
            side_effect=Exception("Processing Error"),
        )

        status, content_type, body = get_data(mock_request)

        assert status == 500
        assert content_type == "text/plain"
        assert body.startswith(b"500 Internal Server Error: ")

    #### POST_DATA() TESTS ####
    # Test post_data with valid JSON data and an authenticated user.
    def test_post_data_success_authenticated_user(self, mock_request, caplog):
        mock_request.method = "POST"
        mock_request.path = "/api/data"
        mock_request.body = b'{"name": "test", "value": 123}'
        mock_request.user = {"username": "postuser", "id": 456}

        status, content_type, body = post_data(mock_request)

        assert status == 200
        assert content_type == "application/json"
        response_data = json.loads(body.decode("utf-8"))
        assert response_data["status"] == "success"
        assert (
            "Received data from postuser: {'name': 'test', 'value': 123}"
            in response_data["message"]
        )
        assert response_data["received_by_user"] == "postuser"

    # Test post_data with valid JSON data but no user information.
    def test_post_data_success_no_user(self, mock_request, caplog):

        mock_request.method = "POST"
        mock_request.path = "/api/data"
        mock_request.body = b'{"item": "new"}'
        mock_request.user = None

        status, content_type, body = post_data(mock_request)

        assert status == 200
        assert content_type == "application/json"
        response_data = json.loads(body.decode("utf-8"))
        assert response_data["status"] == "success"
        assert "Received data from unknown: {'item': 'new'}" in response_data["message"]

    # Test post_data with an empty request body.
    def test_post_data_empty_body(self, mock_request):
        mock_request.method = "POST"
        mock_request.path = "/api/data"
        mock_request.body = b""

        status, content_type, body = post_data(mock_request)
        assert status == 400
        assert content_type == "text/plain"
        assert body == b"400 Bad Request: No data received in request body."

    # Test post_data with an invalid JSON request body.
    def test_post_data_invalid_json(self, mock_request):
        mock_request.method = "POST"
        mock_request.path = "/api/data"
        mock_request.body = b'{"name": "test", "value":}'

        status, content_type, body = post_data(mock_request)
        assert status == 400
        assert content_type == "text/plain"
        assert body == b"400 Bad Request: Invalid JSON in request body."

    # Test post_data with a request body that causes UnicodeDecodeError.
    def test_post_data_unicode_decode_error(self, mock_request):
        mock_request.method = "POST"
        mock_request.path = "/api/data"
        # Simulate a body that cannot be decoded as utf-8
        mock_request.body = b"\xed\xad\xbe"  # Invalid UTF-8 sequence

        status, content_type, body = post_data(mock_request)
        assert status == 400
        assert content_type == "text/plain"
        assert body == b"400 Bad Request: Could not decode request body."

    # Test post_data's error handling for a general exception during processing.
    def test_post_data_general_exception(self, mock_request, mocker):
        mock_request.method = "POST"
        mock_request.path = "/api/data"
        mock_request.body = b'{"valid": "json"}'

        mocker.patch("json.loads", side_effect=Exception("Processing Error"))
        status, content_type, body = post_data(mock_request)

        assert status == 500
        assert content_type == "text/plain"
        assert b"500 Internal Server Error: Processing Error" in body
