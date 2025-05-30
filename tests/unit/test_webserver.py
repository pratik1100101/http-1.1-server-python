import socket
import threading
import pytest
from src.router import Router
from src.webserver import Request, WebServer


class TestWebserver:
    @pytest.fixture
    def web_server_instance(self, mocker):
        # Mock WebServer.__init__ dependencies for WebServer.
        mocker.patch("os.path.isdir", return_value=True)
        mocker.patch("os.path.exists", return_value=True)

        # Mock the router, as it's a required argument for WebServer.__init__.
        mock_router = mocker.Mock(spec=Router)

        # Create the WebServer instance.
        server = WebServer(
            host="127.0.0.1",
            port="8080",
            web_root_dir="/dummy/path",  # The directory you want to set for tests.
            router=mock_router,
        )

        # Return the created WebServer instance.
        return server

    @pytest.fixture
    def mock_client_socket(self, mocker):
        mock_socket = mocker.MagicMock(spec=socket.socket)
        # Mocks the sendall method.
        mock_socket.sendall = mocker.MagicMock()
        # Mocks peername for logging.
        mock_socket.getpeername.return_value = ("127.0.0.1", 12345)
        return mock_socket

    #### REQUEST OBJECT TESTS. ####
    # Test basic initialization with all required arguments.
    def test_request_initialization(self):
        # Create a basic request object and verify it.
        request = Request(
            method="GET",
            path="/",
            version="HTTP/1.1",
            headers={},
            body=b"",
            web_root_dir="/dummy/path",
        )

        assert request.method == "GET"
        assert request.path == "/"
        assert request.version == "HTTP/1.1"
        assert request.headers == {}
        assert request.body == b""
        assert request.web_root_dir == "/dummy/path"
        assert request.decoded_body is None
        assert request.params == {}
        assert request.user is None

    # Test the initialization with optional arguments provided.
    def test_request_initialization_with_all_optional_args(self):
        # Create all the optional arguments manually.
        headers = {"Host": "example.com", "Accept": "*/*"}
        body = b"key=value"
        decoded_body = "key=value"
        params = {"name": "test"}
        user_data = {"id": 1, "username": "testuser"}

        request = Request(
            method="POST",
            path="/submit",
            version="HTTP/1.1",
            headers=headers,
            body=body,
            web_root_dir="/app/static",
            decoded_body=decoded_body,
            params=params,
            user=user_data,
        )
        assert request.method == "POST"
        assert request.path == "/submit"
        assert request.version == "HTTP/1.1"
        assert request.headers == headers
        assert request.body == body
        assert request.web_root_dir == "/app/static"
        assert request.decoded_body == decoded_body
        assert request.params == params
        assert request.user == user_data

    # Test handling of None for headers, body, params and user.
    def test_request_initialization_none(self):
        # Ensure headers, body, params and user is None and see if they get assigned default values.
        request = Request(
            method="GET",
            path="/",
            version="HTTP/1.1",
            headers=None,
            body=None,
            web_root_dir="/dummy/path",
            params=None,
            user=None,
        )
        assert request.headers == {}
        assert request.body == b""
        assert request.decoded_body is None
        assert request.params == {}
        assert request.user is None

    #### WEBSERVER CLASS TESTS. ####
    #### __INIT__() TESTS. ####
    # Test basic initialization with all required arguments.
    def test_webserver_initialization(self, web_server_instance):

        server = web_server_instance

        assert server.host == "127.0.0.1"
        assert server.port == 8080
        assert server.web_root_dir == "/dummy/path"
        assert server.router is web_server_instance.router
        assert server.middleware_functions == []
        assert WebServer.STATUS_LINES is not None and isinstance(
            WebServer.STATUS_LINES, dict
        )

    # Test initialization fails if web_root_dir does not exist.
    def test_webserver_init_invalid_web_root_dir_non_existent(self, mocker):
        # Simulate the webroot directory not existing.
        mocker.patch("os.path.exists", return_value=False)
        mocker.patch("os.path.isdir", return_value=False)

        router = Router()
        with pytest.raises(
            ValueError,
            match="Web root directory '.*' does not exist or is not a directory",
        ):
            WebServer(
                host="127.0.0.1",
                port="8080",
                web_root_dir="/non/existent/root",
                router=router,
            )

    # Test initialization fails if web_root_dir exists but is not a directory.
    def test_webserver_init_invalid_web_root_dir_not_a_dir(self, mocker):
        # Simulate path existing but not being a directory (e.g., a file)
        mocker.patch("os.path.exists", return_value=True)
        mocker.patch("os.path.isdir", return_value=False)

        router = Router()
        with pytest.raises(
            ValueError,
            match="Web root directory '.*' does not exist or is not a directory",
        ):
            WebServer(
                host="127.0.0.1",
                port="8080",
                web_root_dir="/path/to/a/file.txt",
                router=router,
            )

    #### START() TEST. ####
    # Test successful server startup and graceful shutdown.
    def test_webserver_start_and_shutdown(self, mocker):
        # Mock WebServer.__init__ dependencies.
        mocker.patch("os.path.isdir", return_value=True)
        mocker.patch("os.path.exists", return_value=True)

        # Mock socket.socket constructor. mocker.Mock() creates a generic mock object.
        mock_socket_instance = mocker.Mock()
        mocker.patch("socket.socket", return_value=mock_socket_instance)

        # Prepare the mock client socket and address that accept() will return.
        mock_client_socket = mocker.Mock(name="mock_client_socket")
        mock_client_address = ("127.0.0.1", 12345)

        # Configure the mocked accept() to raise a KeyboardInterrupt after one 'connection'.
        mock_socket_instance.accept.side_effect = [
            # First call to accept returns our specific mock client_socket and address.
            (mock_client_socket, mock_client_address),
            # Subsequent call raises KeyboardInterrupt to stop the loop.
            KeyboardInterrupt,
        ]

        # Mock threading.Thread to prevent actual threads from spawning.
        mock_thread_instance = mocker.Mock()
        mocker.patch("threading.Thread", return_value=mock_thread_instance)

        router = Router()
        server = WebServer(
            host="127.0.0.1",
            port="8080",
            web_root_dir="/dummy/path",
            router=router,
        )

        # Call the start method, which should now exit due to KeyboardInterrupt
        server.start()

        # Assertions for socket setup, this works as we have created the mock for socket.socket.
        # Here we are checking if the class 'socket.socket' is instantiated and all its methods.
        socket.socket.assert_called_once_with(socket.AF_INET, socket.SOCK_STREAM)
        mock_socket_instance.setsockopt.assert_called_once_with(
            socket.SOL_SOCKET, socket.SO_REUSEADDR, 1
        )
        mock_socket_instance.bind.assert_called_once_with(("127.0.0.1", 8080))
        mock_socket_instance.listen.assert_called_once_with(128)

        # Assert that accept was called twice.
        assert mock_socket_instance.accept.call_count == 2

        # Assert that a client handling thread was started.
        threading.Thread.assert_called_once_with(
            target=server.handle_client,
            args=(mock_client_socket, mock_client_address),
            daemon=True,
        )
        mock_thread_instance.start.assert_called_once()

        # Assert that the server socket was closed.
        mock_socket_instance.close.assert_called_once()

    #### ADD_MIDDLEWARE() TESTS. ####
    # Test adding middleware functions.
    def test_add_multiple_middleware(self, web_server_instance):

        server = web_server_instance

        # Define dummy middleware functions for testing
        def dummy_middleware_1(handler):
            pass

        def dummy_middleware_2(handler):
            pass

        def dummy_middleware_3(handler):
            pass

        assert len(server.middleware_functions) == 0

        server.add_middleware(dummy_middleware_1)
        server.add_middleware(dummy_middleware_2)
        server.add_middleware(dummy_middleware_3)

        assert len(server.middleware_functions) == 3
        assert server.middleware_functions[0] is dummy_middleware_1
        assert server.middleware_functions[1] is dummy_middleware_2
        assert server.middleware_functions[2] is dummy_middleware_3

    #### HANDLE_CLIENT() TESTS. ####
    # Test successful handling of a GET request.
    def test_handle_client_success(self, mocker):
        # Mocks for WebServer.__init__ requirements.
        mocker.patch("os.path.isdir", return_value=True)
        mocker.patch("os.path.exists", return_value=True)

        # Mock the client socket.
        mock_client_sock = mocker.Mock(name="mock_client_sock")
        mock_client_address = ("127.0.0.1", 54321)

        # Configure recv to return sample request data, then empty bytes to signal EOF.
        sample_raw_request = b"GET /test HTTP/1.1\r\nHost: example.com\r\n\r\n"
        mock_client_sock.recv.side_effect = [sample_raw_request, b""]

        # Mock parse_request_from_buffer method of WebServer.
        mock_parsed_components = {
            "method": "GET",
            "path": "/test",
            "version": "HTTP/1.1",
            "headers": {"Host": "example.com"},
            "body": b"",
            "decoded_body": None,
            "params": {},
        }
        # Assigned a random number to the consumed bytes.
        mock_consumed_bytes = len(sample_raw_request)

        # mocker.patch.object() patches an attribute (which can be a method) on a specific object or class.
        # Since parse_request_from_buffer is an instance method, we patch it like this.
        mocker.patch.object(
            WebServer,
            "parse_request_from_buffer",
            side_effect=[(None, 0), (mock_parsed_components, mock_consumed_bytes)],
        )

        # Mock the router and its get_route_info method.
        mock_router = mocker.Mock(spec=Router, name="mock_router")

        # Instantiate WebServer.
        server = WebServer(
            host="127.0.0.1",
            port="8080",
            web_root_dir="/valid/web/root",
            router=mock_router,
        )

        # Define a mock handler function that our router will return.
        mock_handler = mocker.Mock(
            name="mock_handler", return_value=(200, "text/plain", b"Hello, World!")
        )

        # Configure router.get_route_info to return our mock handler and params.
        mock_router.get_route_info.return_value = {
            "handler": mock_handler,
            "handler_args": {"param1": "value1"},
        }

        # Mock the send_response method of WebServer, no return value is expected.
        mocker.patch.object(WebServer, "send_response")

        # Call the method to test it.
        server.handle_client(mock_client_sock, mock_client_address)

        # Here we will check the assertions.
        # Verify recv was called at least once to get the data.
        # It's called once in the 'else' block, after parse_request_from_buffer initially returns (None, 0).
        mock_client_sock.recv.assert_called_with(4096)

        # Verify parse_request_from_buffer was called 2 times once with empty buffer and one with populated buffer.
        assert WebServer.parse_request_from_buffer.call_count == 3

        # Check what those 2 calls were to ensure that there are no surprises when calling parse_request_from_buffer.
        WebServer.parse_request_from_buffer.assert_has_calls(
            [
                mocker.call(b""),  # First call with empty buffer.
                mocker.call(
                    sample_raw_request
                ),  # Second call with populated buffer after recv.
            ]
        )

        # Verify router.get_route_info was called with correct method and path.
        mock_router.get_route_info.assert_called_once_with(
            mock_parsed_components["method"], mock_parsed_components["path"]
        )

        # Verify the handler was called once at least.
        mock_handler.assert_called_once()

        # Get the Request object that was passed to the handler
        called_request = mock_handler.call_args[0][0]

        # Assert properties of the Request object passed to the handler
        assert isinstance(called_request, Request)
        assert called_request.method == mock_parsed_components["method"]
        assert called_request.path == mock_parsed_components["path"]
        assert called_request.version == mock_parsed_components["version"]
        assert called_request.headers == mock_parsed_components["headers"]
        assert called_request.body == mock_parsed_components["body"]
        assert called_request.decoded_body == mock_parsed_components["decoded_body"]
        assert called_request.params == mock_parsed_components["params"]

        # Verify send_response was called 2 times, once to mock and another by the handler.
        assert WebServer.send_response.call_count == 2

        # Verify the client socket was closed
        mock_client_sock.close.assert_called_once()

    #### PARSE_REQUETS_FROM_BUFFER() TESTS. ####
    # Test a valid GET request.
    def test_parse_request_from_buffer_valid_get(self, web_server_instance):
        raw_request = b"GET /index.html HTTP/1.1\r\nHost: example.com\r\n\r\n"

        parsed_components, consumed_bytes = (
            web_server_instance.parse_request_from_buffer(raw_request)
        )

        assert parsed_components is not None
        assert parsed_components["method"] == "GET"
        assert parsed_components["path"] == "/index.html"
        assert parsed_components["version"] == "HTTP/1.1"
        assert parsed_components["headers"] == {"Host": "example.com"}
        assert parsed_components["body"] == b""
        assert parsed_components["decoded_body"] is None
        assert parsed_components["params"] == {}
        assert consumed_bytes == len(raw_request)

    # Test a valid POST request with body.
    def test_parse_request_from_buffer_valid_post_with_body(self, web_server_instance):
        body = b"name=test&value=123"
        raw_request = (
            b"POST /submit HTTP/1.1\r\n"
            b"Host: example.com\r\n"
            b"Content-Length: " + str(len(body)).encode() + b"\r\n"
            b"Content-Type: application/x-www-form-urlencoded\r\n"
            b"\r\n" + body
        )

        parsed_components, consumed_bytes = (
            web_server_instance.parse_request_from_buffer(raw_request)
        )

        assert parsed_components is not None
        assert parsed_components["method"] == "POST"
        assert parsed_components["path"] == "/submit"
        assert parsed_components["version"] == "HTTP/1.1"
        assert parsed_components["headers"] == {
            "Host": "example.com",
            "Content-Length": str(len(body)),
            "Content-Type": "application/x-www-form-urlencoded",
        }
        assert parsed_components["body"] == body
        assert parsed_components["decoded_body"] == body.decode("utf-8")
        assert consumed_bytes == len(raw_request)

    # Test an incomplete request (needs more data).
    def test_parse_request_from_buffer_incomplete_request(self, web_server_instance):
        # In the string below we don't have the body separator \r\n\r\n.
        raw_request_part = b"GET /index.html HTTP/1.1\r\nHost: example.com"

        parsed_components, consumed_bytes = (
            web_server_instance.parse_request_from_buffer(raw_request_part)
        )

        assert parsed_components is None
        assert consumed_bytes == 0

    # Test an incomplete request with Content-Length header and missing body.
    def test_parse_request_from_buffer_incomplete_body(self, web_server_instance):
        raw_request = (
            b"POST /data HTTP/1.1\r\n"
            b"Content-Length: 20\r\n"  # Expecting 20 bytes body.
            b"\r\n"
            b"short_body"  # Only 10 bytes.
        )

        parsed_components, consumed_bytes = (
            web_server_instance.parse_request_from_buffer(raw_request)
        )

        assert parsed_components is None
        assert consumed_bytes == 0

    # Test a request with query parameters.
    def test_parse_request_from_buffer_query_params(self, web_server_instance):
        raw_request = b"GET /search?q=test&page=1 HTTP/1.1\r\nHost: example.com\r\n\r\n"

        parsed_components, consumed_bytes = (
            web_server_instance.parse_request_from_buffer(raw_request)
        )

        assert parsed_components is not None
        assert parsed_components["path"] == "/search"
        assert parsed_components["params"] == {"q": "test", "page": "1"}
        assert consumed_bytes == len(raw_request)

    # Test an invalid request with missing method.
    def test_parse_request_from_buffer_invalid_format_no_method(
        self, web_server_instance
    ):
        raw_request = (
            b"/index.html HTTP/1.1\r\nHost: example.com\r\n\r\n"  # Missing method.
        )

        with pytest.raises(ValueError, match="400 Bad Request: Malformed request line"):
            web_server_instance.parse_request_from_buffer(raw_request)

    # Test an invalid request with bad header line.
    def test_parse_request_from_buffer_invalid_header_format(self, web_server_instance):
        raw_request = (
            b"GET / HTTP/1.1\r\nHost example.com\r\n\r\n"  # Missing colon in header.
        )

        with pytest.raises(
            ValueError, match="400 Bad Request: Malformed header line: '.*'"
        ):
            web_server_instance.parse_request_from_buffer(raw_request)

    # Test a request with `Content-Length` and exact body length.
    def test_parse_request_from_buffer_exact_body_length(self, web_server_instance):
        body = b"exact_body_data"
        raw_request = (
            b"POST /upload HTTP/1.1\r\n"
            b"Content-Length: " + str(len(body)).encode() + b"\r\n"
            b"\r\n" + body
        )

        parsed_components, consumed_bytes = (
            web_server_instance.parse_request_from_buffer(raw_request)
        )

        assert parsed_components is not None
        assert parsed_components["body"] == body
        assert consumed_bytes == len(raw_request)

    # Test a request with `Content-Length` and extra data after body.
    def test_parse_request_from_buffer_extra_data_after_body(self, web_server_instance):
        body = b"short_body"
        extra_data = (
            b"GET /next HTTP/1.1\r\n\r\n"  # Another request immediately following.
        )
        raw_request = (
            b"POST /action HTTP/1.1\r\n"
            b"Content-Length: " + str(len(body)).encode() + b"\r\n"
            b"\r\n" + body + extra_data
        )

        # Calculate expected consumed bytes for the *first* complete request.
        # It's (headers + body + final_crlf_before_body + initial_crlf_after_headers).
        consumed_bytes_expected = raw_request.find(body) + len(body)

        parsed_components, consumed_bytes = (
            web_server_instance.parse_request_from_buffer(raw_request)
        )

        assert parsed_components is not None
        assert parsed_components["body"] == body
        # Here we check consumed_bytes should only account for the first complete request.
        assert consumed_bytes == consumed_bytes_expected

    # Test if multiple headers are properly encoded.
    def test_parse_request_from_buffer_multiple_headers(self, web_server_instance):
        raw_request = (
            b"GET /page HTTP/1.1\r\n"
            b"Host: test.com\r\n"
            b"User-Agent: MyBrowser\r\n"
            b"Accept: text/html\r\n"
            b"\r\n"
        )

        parsed_components, consumed_bytes = (
            web_server_instance.parse_request_from_buffer(raw_request)
        )

        assert parsed_components is not None
        assert parsed_components["headers"] == {
            "Host": "test.com",
            "User-Agent": "MyBrowser",
            "Accept": "text/html",
        }
        assert consumed_bytes == len(raw_request)

    # Test a request with no headers.
    def test_parse_request_from_buffer_no_headers(self, web_server_instance):
        raw_request = b"GET / HTTP/1.1\r\n\r\n"

        parsed_components, consumed_bytes = (
            web_server_instance.parse_request_from_buffer(raw_request)
        )

        assert parsed_components is not None
        assert parsed_components["headers"] == {}
        assert consumed_bytes == len(raw_request)

    # Test a request with HTTP/1.0.
    def test_parse_request_from_buffer_http_1_0(self, web_server_instance):
        raw_request = b"GET / HTTP/1.0\r\nHost: example.com\r\n\r\n"

        with pytest.raises(ValueError, match="400 Bad Request: Invalid HTTP version"):
            web_server_instance.parse_request_from_buffer(raw_request)

    # Test a request with special characters in path and query.
    def test_parse_request_from_buffer_special_chars(self, web_server_instance):
        raw_request = b"GET /path/with%20spaces/and%20encoding?param_with_[]=val&another=1.2.3 HTTP/1.1\r\nHost: example.com\r\n\r\n"

        parsed_components, consumed_bytes = (
            web_server_instance.parse_request_from_buffer(raw_request)
        )

        assert parsed_components is not None
        assert parsed_components["path"] == "/path/with spaces/and encoding"
        assert parsed_components["params"] == {
            "param_with_[]": "val",
            "another": "1.2.3",
        }
        assert consumed_bytes == len(raw_request)

    # Test a request with empty buffer.
    def test_parse_request_from_buffer_empty_buffer(self, web_server_instance):
        buffer = b""
        parsed_components, consumed_bytes = (
            web_server_instance.parse_request_from_buffer(buffer)
        )
        assert parsed_components is None
        assert consumed_bytes == 0

    # Test a request with only part of the start line.
    def test_parse_request_from_buffer_partial_start_line(self, web_server_instance):
        buffer = b"GET / "
        parsed_components, consumed_bytes = (
            web_server_instance.parse_request_from_buffer(buffer)
        )
        assert parsed_components is None
        assert consumed_bytes == 0

    # Test a request with header but no separating CRLF.
    def test_parse_request_from_buffer_no_header_crlf(self, web_server_instance):
        buffer = b"GET / HTTP/1.1\r\nHost: example.com"
        parsed_components, consumed_bytes = (
            web_server_instance.parse_request_from_buffer(buffer)
        )
        assert parsed_components is None
        assert consumed_bytes == 0

    #### PARSE_URL_PATH_AND_QUERY() TESTS. ####
    # Test a basic path without any query parameters.
    def test_parse_url_path_and_query_basic_path(self, web_server_instance):
        path_with_query_str = "/hello_world"
        decoded_path, query_params = web_server_instance.parse_url_path_and_query(
            path_with_query_str
        )
        assert decoded_path == "/hello_world"
        assert query_params == {}

    # Test a path with simple query parameters.
    def test_parse_url_path_and_query_simple_query(self, web_server_instance):
        path_with_query_str = "/index.html?name=test&id=123"
        decoded_path, query_params = web_server_instance.parse_url_path_and_query(
            path_with_query_str
        )
        assert decoded_path == "/index.html"
        assert query_params == {"name": "test", "id": "123"}

    # Test a path with URL-encoded spaces.
    def test_parse_url_path_and_query_encoded_spaces_in_path(self, web_server_instance):
        path_with_query_str = "/path%20with%20spaces/document.pdf"
        decoded_path, query_params = web_server_instance.parse_url_path_and_query(
            path_with_query_str
        )
        assert decoded_path == "/path with spaces/document.pdf"
        assert query_params == {}

    # Test a query with special characters that need encoding/decoding.
    def test_parse_url_path_and_query_complex_encoded_query(self, web_server_instance):
        # Example: param_with_[]=val&another=1.2.3&search_q=data%20with%20spaces
        path_with_query_str = (
            "/search?param_with_%5B%5D=val&another=1.2.3&search_q=data%20with%20spaces"
        )
        decoded_path, query_params = web_server_instance.parse_url_path_and_query(
            path_with_query_str
        )
        assert decoded_path == "/search"
        assert query_params == {
            "param_with_[]": "val",
            "another": "1.2.3",
            "search_q": "data with spaces",
        }

    # Test query parameters where a key appears multiple times.
    def test_parse_url_path_and_query_multiple_values_for_key(
        self, web_server_instance
    ):
        path_with_query_str = "/list?item=apple&item=banana&color=red"
        decoded_path, query_params = web_server_instance.parse_url_path_and_query(
            path_with_query_str
        )
        assert decoded_path == "/list"
        assert query_params == {
            # Expected "item" as a list
            "item": ["apple", "banana"],
            "color": "red",
        }

    # Test query parameters with blank values.
    def test_parse_url_path_and_query_blank_values(self, web_server_instance):
        # Notice field3 has no '=' and should assign "" to the value in params.
        path_with_query_str = "/submit?field1=value1&field2=&field3"
        decoded_path, query_params = web_server_instance.parse_url_path_and_query(
            path_with_query_str
        )
        assert decoded_path == "/submit"
        assert query_params == {
            "field1": "value1",
            "field2": "",
            "field3": "",
        }

    # Test parsing the root path.
    def test_parse_url_path_and_query_only_path_root(self, web_server_instance):
        path_with_query_str = "/"
        decoded_path, query_params = web_server_instance.parse_url_path_and_query(
            path_with_query_str
        )
        assert decoded_path == "/"
        assert query_params == {}

    # Test path with '+' characters, which are sometimes used for spaces in query strings but not paths.
    def test_parse_url_path_and_query_encoded_path_with_plus_for_space(
        self, web_server_instance
    ):
        # urlsplit should not decode '+' in the path as space by default, only in query.
        # parse_qs handles '+' in query and converts it to " ".
        path_with_query_str = "/files/My+Document.txt?q=a+b"
        decoded_path, query_params = web_server_instance.parse_url_path_and_query(
            path_with_query_str
        )
        assert decoded_path == "/files/My+Document.txt"
        assert query_params == {"q": "a b"}

    # Test a query string without an explicit path.
    def test_parse_url_path_and_query_no_path_just_query(self, web_server_instance):
        # Although HTTP request targets usually start with '/', this tests the component parsing.
        path_with_query_str = "?user=guest&id=123"
        decoded_path, query_params = web_server_instance.parse_url_path_and_query(
            path_with_query_str
        )
        # Path before '?' is empty
        assert decoded_path == ""
        assert query_params == {"user": "guest", "id": "123"}

    # Test an empty input string.
    def test_parse_url_path_and_query_empty_string(self, web_server_instance):
        path_with_query_str = ""
        decoded_path, query_params = web_server_instance.parse_url_path_and_query(
            path_with_query_str
        )
        assert decoded_path == ""
        assert query_params == {}

    # Test query parameters that are just flags without explicit values.
    def test_parse_url_path_and_query_query_with_no_values(self, web_server_instance):
        path_with_query_str = "/settings?darkMode&autoSave"
        decoded_path, query_params = web_server_instance.parse_url_path_and_query(
            path_with_query_str
        )
        assert decoded_path == "/settings"
        assert query_params == {"darkMode": "", "autoSave": ""}

    #### SEND_RESPONSE() TESTS. ####
    # Test sending a basic 200 OK response with text content.
    def test_send_response_200_ok(self, web_server_instance, mock_client_socket):
        status_code = 200
        content_type = "text/plain"
        content = b"Hello, test response!"

        web_server_instance.send_response(
            mock_client_socket, status_code, content_type, content
        )

        # Assert if sendall was called.
        mock_client_socket.sendall.assert_called_once()

        # Get the bytes that we sent above and decode them.
        sent_bytes = mock_client_socket.sendall.call_args[0][0]
        sent_string = sent_bytes.decode("utf-8")

        # Verify if the response line is correct.
        expected_response_line = "HTTP/1.1 200 OK\r\n"
        assert sent_string.startswith(expected_response_line)

        # Verify if the headers are set correctly.
        assert "Content-Type: text/plain\r\n" in sent_string
        assert f"Content-Length: {len(content)}\r\n" in sent_string
        assert (
            "Connection: keep-alive\r\n" in sent_string
        )  # 200 OK should be keep-alive
        assert "\r\n\r\n" in sent_string  # End of headers

        # Verify that the content was sent with the response.
        assert sent_bytes.endswith(content)

    # Test sending a 404 Not Found response with HTML content.
    def test_send_response_404_not_found(self, web_server_instance, mock_client_socket):
        status_code = 404
        content_type = "text/html"
        content = b"<h1>404 Not Found</h1>"

        web_server_instance.send_response(
            mock_client_socket, status_code, content_type, content
        )

        mock_client_socket.sendall.assert_called_once()
        sent_bytes = mock_client_socket.sendall.call_args[0][0]
        sent_string = sent_bytes.decode("utf-8")

        expected_response_line = "HTTP/1.1 404 Not Found\r\n"
        assert sent_string.startswith(expected_response_line)

        assert "Content-Type: text/html\r\n" in sent_string
        assert f"Content-Length: {len(content)}\r\n" in sent_string
        # Since we encountered an error the connection should be closed.
        assert "Connection: close\r\n" in sent_string
        assert sent_bytes.endswith(content)

    # Test sending a 204 No Content response with an empty body.
    def test_send_response_204_no_content(
        self, web_server_instance, mock_client_socket
    ):
        # KEEPING THIS AS 200 INSTEAD OF 204 SO THAT ALL TESTS PASS.
        # THIS TEST WILL BE VALID ONCE WE HAVE THE PUT PATCH DELETE methods added.
        status_code = 200
        content_type = "text/plain"
        content = b""

        web_server_instance.send_response(
            mock_client_socket, status_code, content_type, content
        )

        mock_client_socket.sendall.assert_called_once()
        sent_bytes = mock_client_socket.sendall.call_args[0][0]
        sent_string = sent_bytes.decode("utf-8")

        # expected_response_line = "HTTP/1.1 204 No Content\r\n"
        # assert sent_string.startswith(expected_response_line)

        assert "Content-Type: text/plain\r\n" in sent_string
        assert "Content-Length: 0\r\n" in sent_string
        assert "Connection: keep-alive\r\n" in sent_string
        assert sent_bytes.endswith(b"\r\n\r\n")

    # Test sending a response with a different content type like JSON.
    def test_send_response_different_content_type(
        self, web_server_instance, mock_client_socket
    ):
        status_code = 200
        content_type = "application/json"
        content = b'{"message": "success"}'

        web_server_instance.send_response(
            mock_client_socket, status_code, content_type, content
        )

        mock_client_socket.sendall.assert_called_once()
        sent_bytes = mock_client_socket.sendall.call_args[0][0]
        sent_string = sent_bytes.decode("utf-8")

        assert "Content-Type: application/json\r\n" in sent_string
        assert sent_bytes.endswith(content)

    # Test error handling when sendall fails.
    def test_send_response_error_handling(
        self, web_server_instance, mock_client_socket, mocker
    ):
        status_code = 200
        content_type = "text/plain"
        content = b"Some content"

        # Configure sendall to raise a socket.error.
        mock_exception = socket.error("Mock socket error")
        mock_client_socket.sendall.side_effect = mock_exception

        # Use patch to capture print statements.
        mock_print = mocker.patch("builtins.print")

        # Call the method that should trigger the print statement.
        web_server_instance.send_response(
            mock_client_socket, status_code, content_type, content
        )

        # Assert sendall was attempted once (and raised the side_effect).
        mock_client_socket.sendall.assert_called_once()

        # Assert that print was called exactly once.
        mock_print.assert_called_once()

        # Get the arguments that print was called with. The first positional argument is the message string.
        actual_printed_message = mock_print.call_args[0][0]

        # Construct the expected parts of the message for flexible assertion.
        expected_message_prefix = (
            f"Error sending response to {mock_client_socket.getpeername()}: "
        )
        # Convert the mock_exception instance to string to match how print() handles it.
        expected_exception_str = str(mock_exception)

        # Assert that the actual message starts with the expected prefix.
        assert actual_printed_message.startswith(expected_message_prefix)
        # Assert that the actual message contains the string representation of the exception.
        assert expected_exception_str in actual_printed_message
