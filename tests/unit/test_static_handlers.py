import pytest
import os
from src.webserver import Request
from src.handlers import static_handlers
import mimetypes


class TestStaticHandler:

    @pytest.fixture
    def mock_request(self, mocker):
        mock_req = mocker.Mock(spec=Request)
        # We only need web_root_dir for these tests.
        # Other attributes like method, path, headers, body, user are not used in serve_static_file.
        mock_req.web_root_dir = "webroot"
        return mock_req

    @pytest.fixture(autouse=True)
    def setup_mocker_for_class(self, mocker):
        self._mocker = mocker
        self.mock_os_path_isfile = mocker.patch("os.path.isfile")
        self.mock_open = mocker.patch("builtins.open")
        self.mock_mimetypes_guess_type = mocker.patch("mimetypes.guess_type")
        # We use the original os.path.join as side_effect to ensure correct path construction
        # while still being able to assert calls to it.
        self.mock_os_path_join = mocker.patch("os.path.join", side_effect=os.path.join)
        # Mock mimetypes.add_type to prevent global state modification
        self.mock_mimetypes_add_type = mocker.patch("mimetypes.add_type")

    #### SERVER_STATIC_FILE() TESTS ####
    # Test successfully serving an HTML file.
    def test_serve_existing_html_file(self, mock_request):

        filepath = "index.html"
        file_content = b"<h1>Hello, world!</h1>"
        self.mock_os_path_isfile.return_value = True
        self.mock_open.return_value.__enter__.return_value.read.return_value = (
            file_content
        )
        self.mock_mimetypes_guess_type.return_value = ("text/html", None)

        status, content_type, content = static_handlers.serve_static_file(
            mock_request, filepath
        )

        assert status == 200
        assert content_type == "text/html"
        assert content == file_content
        self.mock_os_path_join.assert_called_with(mock_request.web_root_dir, filepath)
        self.mock_os_path_isfile.assert_called_with(
            os.path.join(mock_request.web_root_dir, filepath)
        )
        self.mock_open.assert_called_with(
            os.path.join(mock_request.web_root_dir, filepath), "rb"
        )
        self.mock_mimetypes_guess_type.assert_called_with(
            os.path.join(mock_request.web_root_dir, filepath)
        )

    # Test successfully serving a JavaScript file with correct content type.
    def test_serve_existing_js_file(self, mock_request):

        filepath = "script.js"
        file_content = b"console.log('Hello from JS!');"
        self.mock_os_path_isfile.return_value = True
        self.mock_open.return_value.__enter__.return_value.read.return_value = (
            file_content
        )
        self.mock_mimetypes_guess_type.return_value = ("application/javascript", None)

        status, content_type, content = static_handlers.serve_static_file(
            mock_request, filepath
        )

        assert status == 200
        assert content_type == "application/javascript"
        assert content == file_content
        self.mock_os_path_join.assert_called_with(mock_request.web_root_dir, filepath)
        self.mock_os_path_isfile.assert_called_with(
            os.path.join(mock_request.web_root_dir, filepath)
        )
        self.mock_open.assert_called_with(
            os.path.join(mock_request.web_root_dir, filepath), "rb"
        )
        self.mock_mimetypes_guess_type.assert_called_with(
            os.path.join(mock_request.web_root_dir, filepath)
        )

    # Test successfully serving a CSS file with correct content type.
    def test_serve_existing_css_file(self, mock_request):

        filepath = "style.css"
        file_content = b"body { color: red; }"
        self.mock_os_path_isfile.return_value = True
        self.mock_open.return_value.__enter__.return_value.read.return_value = (
            file_content
        )
        self.mock_mimetypes_guess_type.return_value = ("text/css", None)

        status, content_type, content = static_handlers.serve_static_file(
            mock_request, filepath
        )

        assert status == 200
        assert content_type == "text/css"
        assert content == file_content
        self.mock_os_path_join.assert_called_with(mock_request.web_root_dir, filepath)
        self.mock_os_path_isfile.assert_called_with(
            os.path.join(mock_request.web_root_dir, filepath)
        )
        self.mock_open.assert_called_with(
            os.path.join(mock_request.web_root_dir, filepath), "rb"
        )
        self.mock_mimetypes_guess_type.assert_called_with(
            os.path.join(mock_request.web_root_dir, filepath)
        )

    # Test handling requests for non-existent static files (should return 404).
    def test_serve_non_existent_file(self, mock_request):

        filepath = "non_existent.html"
        self.mock_os_path_isfile.return_value = False

        status, content_type, content = static_handlers.serve_static_file(
            mock_request, filepath
        )

        assert status == 404
        assert content_type == "text/plain"
        assert b"404 Not Found: Static file not found." in content
        self.mock_os_path_join.assert_called_with(mock_request.web_root_dir, filepath)
        self.mock_os_path_isfile.assert_called_with(
            os.path.join(mock_request.web_root_dir, filepath)
        )
        self.mock_open.assert_not_called()

    # Test handling a general exception during file serving.
    def test_serve_static_file_general_exception(self, mock_request):

        filepath = "error_file.txt"
        self.mock_os_path_isfile.return_value = True
        self.mock_open.return_value.__enter__.return_value.read.side_effect = IOError(
            "Disk full"
        )

        # Mock the print function to prevent actual output during the test
        self._mocker.patch("builtins.print")

        status, content_type, content = static_handlers.serve_static_file(
            mock_request, filepath
        )

        assert status == 500
        assert content_type == "text/plain"
        assert (
            b"500 Internal Server Error: Could not serve file (Disk full)." in content
        )
        self.mock_os_path_join.assert_called_with(mock_request.web_root_dir, filepath)
        self.mock_os_path_isfile.assert_called_with(
            os.path.join(mock_request.web_root_dir, filepath)
        )
        self.mock_open.assert_called_with(
            os.path.join(mock_request.web_root_dir, filepath), "rb"
        )

    # Test handling directory traversal attempts (e.g., /../etc/passwd).
    def test_directory_traversal_attempt(self, mock_request):

        filepath = "../etc/passwd"
        expected_full_path = os.path.join(mock_request.web_root_dir, filepath)

        self.mock_os_path_isfile.return_value = False

        status, content_type, content = static_handlers.serve_static_file(
            mock_request, filepath
        )

        assert status == 404
        assert content_type == "text/plain"
        assert b"404 Not Found: Static file not found." in content
        self.mock_os_path_join.assert_called_with(mock_request.web_root_dir, filepath)
        self.mock_os_path_isfile.assert_called_with(expected_full_path)
        self.mock_open.assert_not_called()
