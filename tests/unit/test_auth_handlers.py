import datetime
import json
from types import SimpleNamespace
import pytest
from src.handlers.auth_handlers import register_user, login_user, get_user_profile
from src.webserver import Request


class TestAuthHandlers:
    # Remember all the .patch() need to refer to the place where it is used, in this case
    # "src.handlers.auth_handlers", and not their original place like "src.database.db_config.start_db"
    @pytest.fixture
    def mock_db_session(self, mocker):
        mock_session = mocker.MagicMock()
        mocker.patch(
            "src.handlers.auth_handlers.start_db",
            return_value=mocker.MagicMock(
                __enter__=lambda self: mock_session,
                __exit__=lambda self, exc_type, exc_val, exc_tb: None,
            ),
        )
        yield mock_session

    @pytest.fixture
    def mock_user_repository(self, mocker):
        mock_create_user = mocker.patch("src.handlers.auth_handlers.create_user")
        mock_get_user_by_username = mocker.patch(
            "src.handlers.auth_handlers.get_user_by_username"
        )

        return SimpleNamespace(
            create_user=mock_create_user, get_user_by_username=mock_get_user_by_username
        )

    @pytest.fixture
    def mock_auth_utils(self, mocker):
        mock_hash_password = mocker.patch("src.handlers.auth_handlers.hash_password")
        mock_check_password = mocker.patch("src.handlers.auth_handlers.check_password")
        mock_create_jwt_token = mocker.patch(
            "src.handlers.auth_handlers.create_jwt_token"
        )

        return SimpleNamespace(
            hash_password=mock_hash_password,
            check_password=mock_check_password,
            create_jwt_token=mock_create_jwt_token,
        )

    #### REGISTER_USER() ####
    # Test successful user registration.
    def test_register_user_success(
        self, mock_db_session, mock_user_repository, mock_auth_utils, mocker
    ):
        mock_user_repository.get_user_by_username.return_value = None
        mock_auth_utils.hash_password.return_value = "hashed_password"
        mock_user_repository.create_user.return_value = mocker.MagicMock(
            id=1, username="testuser", role="user"
        )

        mock_request = mocker.Mock(spec=Request)
        mock_request.method = "POST"
        mock_request.path = "/api/register"
        mock_request.headers = {}
        mock_request.body = b""
        mock_request.decoded_body = (
            '{"username": "testuser", "password": "password123"}'
        )

        status, content_type, body = register_user(mock_request)

        assert status == 201
        assert content_type == "application/json"
        assert json.loads(body)["message"] == "User registered successfully"
        assert json.loads(body)["username"] == "testuser"
        mock_user_repository.get_user_by_username.assert_called_once_with(
            mock_db_session, "testuser"
        )
        mock_auth_utils.hash_password.assert_called_once_with("password123")
        mock_user_repository.create_user.assert_called_once_with(
            mock_db_session,
            username="testuser",
            hashed_password="hashed_password",
            role="user",
        )

    # Test registration with an existing username.
    def test_register_user_existing_username(
        self, mock_db_session, mock_user_repository, mock_auth_utils, mocker
    ):
        mock_user_repository.get_user_by_username.return_value = mocker.MagicMock()

        mock_request = mocker.Mock(spec=Request)
        mock_request.method = "POST"
        mock_request.path = "/api/register"
        mock_request.headers = {}
        mock_request.body = b""
        mock_request.decoded_body = (
            '{"username": "existinguser", "password": "password123"}'
        )

        status, content_type, body = register_user(mock_request)

        assert status == 409
        assert content_type == "application/json"
        assert json.loads(body)["error"] == "User 'existinguser' already exists"
        mock_user_repository.get_user_by_username.assert_called_once_with(
            mock_db_session, "existinguser"
        )
        mock_auth_utils.hash_password.assert_not_called()
        mock_user_repository.create_user.assert_not_called()

    # Test registration with missing username or password.
    def test_register_user_missing_credentials(self, mocker):

        mock_request = mocker.Mock(spec=Request)
        mock_request.method = "POST"
        mock_request.path = "/api/register"
        mock_request.headers = {}
        mock_request.body = b""
        mock_request.decoded_body = '{"username": "testuser"}'

        status, content_type, body = register_user(mock_request)

        assert status == 400
        assert content_type == "application/json"
        assert json.loads(body)["error"] == "Username and password are required."

        mock_request.decoded_body = '{"password": "password123"}'
        status, content_type, body = register_user(mock_request)

        assert status == 400
        assert content_type == "application/json"
        assert json.loads(body)["error"] == "Username and password are required."

    # Test registration with invalid JSON in the request body.
    def test_register_user_invalid_json(self, mocker):

        mock_request = mocker.Mock(spec=Request)
        mock_request.method = "POST"
        mock_request.path = "/api/register"
        mock_request.headers = {}
        mock_request.body = b"invalid json"
        mock_request.decoded_body = "invalid json"

        status, content_type, body = register_user(mock_request)

        assert status == 400
        assert content_type == "text/plain"
        assert body == b"400 Bad Request: Invalid JSON in request body."

    # Test registration with a non-POST method.
    def test_register_user_method_not_allowed(self, mocker):

        mock_request = mocker.Mock(spec=Request)
        mock_request.method = "GET"
        mock_request.path = "/api/register"
        mock_request.headers = {}
        mock_request.body = b""
        mock_request.decoded_body = ""

        status, content_type, body = register_user(mock_request)

        assert status == 405
        assert content_type == "text/plain"
        assert body == b"405 Method Not Allowed"

    # Test registration with an empty request body.
    def test_register_user_empty_body(self, mocker):

        mock_request = mocker.Mock(spec=Request)
        mock_request.method = "POST"
        mock_request.path = "/api/register"
        mock_request.headers = {}
        mock_request.body = b""
        mock_request.decoded_body = ""

        status, content_type, body = register_user(mock_request)

        assert status == 400
        assert content_type == "text/plain"
        assert body == b"400 Bad Requesr: Request body is empty."

    #### LOGIN_USER() TESTS ####
    # Test successful user login with correct credentials.
    def test_login_user_success(
        self, mock_db_session, mock_user_repository, mock_auth_utils, mocker
    ):

        mock_user = mocker.MagicMock(
            username="testuser", hashed_password="hashed_password", role="user"
        )
        mock_user_repository.get_user_by_username.return_value = mock_user
        mock_auth_utils.check_password.return_value = True
        mock_auth_utils.create_jwt_token.return_value = "mock_jwt_token"

        mock_request = mocker.Mock(spec=Request)
        mock_request.method = "POST"
        mock_request.path = "/api/login"
        mock_request.headers = {}
        mock_request.body = b'{"username": "testuser", "password": "password123"}'
        mock_request.decoded_body = (
            '{"username": "testuser", "password": "password123"}'
        )

        status, content_type, body = login_user(mock_request)

        assert status == 200
        assert content_type == "application/json"
        assert json.loads(body)["message"] == "Login Sucessful"
        assert json.loads(body)["token"] == "mock_jwt_token"
        mock_user_repository.get_user_by_username.assert_called_once_with(
            mock_db_session, "testuser"
        )
        mock_auth_utils.check_password.assert_called_once_with(
            "password123", "hashed_password"
        )
        mock_auth_utils.create_jwt_token.assert_called_once_with(
            {"username": "testuser", "role": "user"}
        )

    # Test failed login with incorrect credentials.
    def test_login_user_incorrect_credentials(
        self, mock_db_session, mock_user_repository, mock_auth_utils, mocker
    ):

        mock_user = mocker.MagicMock(
            username="testuser", hashed_password="hashed_password", role="user"
        )
        mock_user_repository.get_user_by_username.return_value = mock_user
        mock_auth_utils.check_password.return_value = False

        mock_request = mocker.Mock(spec=Request)
        mock_request.method = "POST"
        mock_request.path = "/api/login"
        mock_request.headers = {}
        mock_request.body = b'{"username": "testuser", "password": "wrongpassword"}'
        mock_request.decoded_body = (
            '{"username": "testuser", "password": "wrongpassword"}'
        )

        status, content_type, body = login_user(mock_request)

        assert status == 401
        assert content_type == "application/json"
        assert json.loads(body)["error"] == "Invalid credentials"
        mock_user_repository.get_user_by_username.assert_called_once_with(
            mock_db_session, "testuser"
        )
        mock_auth_utils.check_password.assert_called_once_with(
            "wrongpassword", "hashed_password"
        )
        mock_auth_utils.create_jwt_token.assert_not_called()

    # Test login when the user does not exist in the database.
    def test_login_user_missing_user(
        self, mock_db_session, mock_user_repository, mock_auth_utils, mocker
    ):

        mock_user_repository.get_user_by_username.return_value = None

        mock_request = mocker.Mock(spec=Request)
        mock_request.method = "POST"
        mock_request.path = "/api/login"
        mock_request.headers = {}
        mock_request.body = (
            b'{"username": "nonexistentuser", "password": "password123"}'
        )
        mock_request.decoded_body = (
            '{"username": "nonexistentuser", "password": "password123"}'
        )

        status, content_type, body = login_user(mock_request)

        assert status == 401
        assert content_type == "application/json"
        assert json.loads(body)["error"] == "Invalid credentials"
        mock_user_repository.get_user_by_username.assert_called_once_with(
            mock_db_session, "nonexistentuser"
        )
        mock_auth_utils.check_password.assert_not_called()
        mock_auth_utils.create_jwt_token.assert_not_called()

    # Test login with missing username or password.
    def test_login_user_missing_credentials(self, mocker):

        mock_request = mocker.Mock(spec=Request)
        mock_request.method = "POST"
        mock_request.path = "/api/login"
        mock_request.headers = {}
        mock_request.body = b'{"username": "testuser"}'
        mock_request.decoded_body = '{"username": "testuser"}'

        status, content_type, body = login_user(mock_request)

        assert status == 400
        assert content_type == "application/json"
        assert json.loads(body)["error"] == "Username and password are required."

        mock_request.body = b'{"password": "password123"}'
        mock_request.decoded_body = '{"password": "password123"}'
        status, content_type, body = login_user(mock_request)

        assert status == 400
        assert content_type == "application/json"
        assert json.loads(body)["error"] == "Username and password are required."

    # Test login with invalid JSON in the request body.
    def test_login_user_invalid_json(self, mocker):

        mock_request = mocker.Mock(spec=Request)
        mock_request.method = "POST"
        mock_request.path = "/api/login"
        mock_request.headers = {}
        mock_request.body = b"invalid json"
        mock_request.decoded_body = "invalid json"

        status, content_type, body = login_user(mock_request)

        assert status == 400
        assert content_type == "text/plain"
        assert body == b"400 Bad Request: Invalid JSON in request body."

    # Test login with a non-POST method.
    def test_login_user_method_not_allowed(self, mocker):

        mock_request = mocker.Mock(spec=Request)
        mock_request.method = "GET"
        mock_request.path = "/api/login"
        mock_request.headers = {}
        mock_request.body = b""
        mock_request.decoded_body = ""

        status, content_type, body = login_user(mock_request)

        assert status == 405
        assert content_type == "text/plain"
        assert body == b"405 Method Not Allowed"

    # Test login with an empty request body.
    def test_login_user_empty_body(self, mocker):

        mock_request = mocker.Mock(spec=Request)
        mock_request.method = "POST"
        mock_request.path = "/api/login"
        mock_request.headers = {}
        mock_request.body = b""
        mock_request.decoded_body = ""

        status, content_type, body = login_user(mock_request)

        assert status == 400
        assert content_type == "text/plain"
        assert body == b"400 Bad Requesr: Request body is empty."

    #### GET_USER_PROFILE() TESTS ####
    # Test successful retrieval of user profile.
    def test_get_user_profile_success(
        self, mock_db_session, mock_user_repository, mocker
    ):

        mock_user = mocker.MagicMock(
            username="testuser",
            role="user",
            created_at=datetime.datetime(2025, 1, 1, 12, 30, 0),
        )
        mock_user_repository.get_user_by_username.return_value = mock_user

        mock_request = mocker.Mock(spec=Request)
        mock_request.method = "GET"
        mock_request.path = "/api/profile"
        mock_request.headers = {}
        mock_request.body = b""
        mock_request.decoded_body = ""
        mock_request.user = {
            "username": "testuser",
            "role": "user",
        }

        status, content_type, body = get_user_profile(mock_request)

        assert status == 200
        assert content_type == "application/json"
        response_data = json.loads(body)
        assert response_data["message"] == "User profile data"
        assert response_data["username_from_token"] == "testuser"
        assert response_data["role_from_token"] == "user"
        assert response_data["username_from_db"] == "testuser"
        assert response_data["created_at"] == "2025-01-01T12:30:00"
        mock_user_repository.get_user_by_username.assert_called_once_with(
            mock_db_session, "testuser"
        )

    # Test get_user_profile when request.user is not set.
    def test_get_user_profile_unauthorized_no_user_in_request(self, mocker):

        mock_request = mocker.Mock(spec=Request)
        mock_request.method = "GET"
        mock_request.path = "/api/profile"
        mock_request.headers = {}
        mock_request.body = b""
        mock_request.decoded_body = ""
        # mock_request.user is intentionally not set

        status, content_type, body = get_user_profile(mock_request)

        assert status == 401
        assert content_type == "text/plain"
        assert body == b"401 Unauthorized: User data missing."

    # Test get_user_profile when the user from the token is not found in the database.
    def test_get_user_profile_user_not_found_in_db(
        self, mock_db_session, mock_user_repository, mocker
    ):

        mock_user_repository.get_user_by_username.return_value = None
        mock_request = mocker.Mock(spec=Request)
        mock_request.method = "GET"
        mock_request.path = "/api/profile"
        mock_request.headers = {}
        mock_request.body = b""
        mock_request.user = {"username": "nonexistent", "role": "user"}

        status, content_type, body = get_user_profile(mock_request)

        assert status == 404
        assert content_type == "application/json"
        assert json.loads(body)["error"] == "User not found in database."
        mock_user_repository.get_user_by_username.assert_called_once_with(
            mock_db_session, "nonexistent"
        )

    # Test get_user_profile with an invalid username type in the token payload.
    def test_get_user_profile_invalid_username_in_token(self, mocker):

        mock_request = mocker.Mock(spec=Request)
        mock_request.method = "GET"
        mock_request.path = "/api/profile"
        mock_request.headers = {}
        mock_request.body = b""
        mock_request.decoded_body = ""
        mock_request.user = {"username": 123, "role": "user"}

        status, content_type, body = get_user_profile(mock_request)

        assert status == 400
        assert content_type == "application/json"
        assert (
            json.loads(body)["error"]
            == "Bad Request: User ID missing or invalid in token payload."
        )

    # Test get_user_profile with a non-GET method.
    def test_get_user_profile_method_not_allowed(self, mocker):

        mock_request = mocker.Mock(spec=Request)
        mock_request.method = "POST"
        mock_request.path = "/api/profile"
        mock_request.headers = {}
        mock_request.body = b""
        mock_request.decoded_body = ""
        mock_request.user = {"username": "testuser", "role": "user"}

        status, content_type, body = get_user_profile(mock_request)

        assert status == 405
        assert content_type == "text/plain"
        assert body == b"405 Method Not Allowed"
