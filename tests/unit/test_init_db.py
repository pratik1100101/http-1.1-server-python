import pytest
from src.database.init_db import init_db


class TestInitDb:

    # Fixture to mock common database-related dependencies for init_db tests.
    @pytest.fixture
    def mock_db_dependencies(self, mocker):

        mock_base = mocker.patch("src.database.init_db.Base")
        mock_session_local = mocker.patch("src.database.init_db.SessionLocal")
        mock_get_user_by_username = mocker.patch(
            "src.database.init_db.get_user_by_username"
        )
        mock_hash_password = mocker.patch("src.database.init_db.hash_password")
        mock_create_user = mocker.patch("src.database.init_db.create_user")

        # Mock the session object and its common methods.
        mock_session = mocker.MagicMock()
        mock_session_local.return_value = mock_session

        return {
            "Base": mock_base,
            "SessionLocal": mock_session_local,
            "get_user_by_username": mock_get_user_by_username,
            "hash_password": mock_hash_password,
            "create_user": mock_create_user,
            "session": mock_session,
        }

    # Test that init_db creates tables and seeds the admin user when it doesn't exist.
    def test_init_db_creates_tables_and_seeds_admin_user(
        self, mock_db_dependencies, mocker
    ):
        # Unpack mocks from the imported fixture.
        mock_base = mock_db_dependencies["Base"]
        mock_session_local = mock_db_dependencies["SessionLocal"]
        mock_get_user_by_username = mock_db_dependencies["get_user_by_username"]
        mock_hash_password = mock_db_dependencies["hash_password"]
        mock_create_user = mock_db_dependencies["create_user"]
        mock_session = mock_db_dependencies["session"]

        # Simulate admin user not existing.
        mock_get_user_by_username.return_value = None

        # Simulate password hashing.
        mock_hash_password.return_value = "hashed_admin_password"

        init_db()

        # Assert Base.metadata.create_all was called.
        mock_base.metadata.create_all.assert_called_once_with(bind=mocker.ANY)

        # Assert get_user_by_username was called.
        mock_get_user_by_username.assert_called_once_with(mock_session, "admin")

        # Assert hash_password was called.
        mock_hash_password.assert_called_once_with("admin_password")

        # Assert create_user was called with correct arguments.
        mock_create_user.assert_called_once_with(
            mock_session, "admin", "hashed_admin_password", "admin"
        )

        # Assert session.close was called.
        mock_session.close.assert_called_once()

    # Test that init_db does not recreate the admin user if it already exists.
    def test_init_db_handles_existing_admin_user(self, mock_db_dependencies, mocker):
        # Unpack mocks from the imported fixture.
        mock_base = mock_db_dependencies["Base"]
        mock_session_local = mock_db_dependencies["SessionLocal"]
        mock_get_user_by_username = mock_db_dependencies["get_user_by_username"]
        mock_hash_password = mock_db_dependencies["hash_password"]
        mock_create_user = mock_db_dependencies["create_user"]
        mock_session = mock_db_dependencies["session"]

        # Simulate admin user already existing.
        mock_get_user_by_username.return_value = mocker.MagicMock(username="admin")

        init_db()

        # Assert Base.metadata.create_all was called.
        mock_base.metadata.create_all.assert_called_once_with(bind=mocker.ANY)

        # Assert get_user_by_username was called.
        mock_get_user_by_username.assert_called_once_with(mock_session, "admin")

        # Assert hash_password was NOT called.
        mock_hash_password.assert_not_called()

        # Assert create_user was NOT called.
        mock_create_user.assert_not_called()

        # Assert session.close was called.
        mock_session.close.assert_called_once()

    # Test that init_db handles errors during admin user creation by rolling back the session.
    def test_init_db_error_handling_during_admin_creation_rollbacks(
        self, mock_db_dependencies, mocker
    ):
        # Unpack mocks from the imported fixture.
        mock_base = mock_db_dependencies["Base"]
        mock_session_local = mock_db_dependencies["SessionLocal"]
        mock_get_user_by_username = mock_db_dependencies["get_user_by_username"]
        mock_hash_password = mock_db_dependencies["hash_password"]
        mock_create_user = mock_db_dependencies["create_user"]
        mock_session = mock_db_dependencies["session"]

        # Simulate admin user not existing.
        mock_get_user_by_username.return_value = None

        # Simulate an exception during create_user.
        mock_create_user.side_effect = Exception("Database write error")

        with pytest.raises(Exception, match="Database write error"):
            init_db()

        # Assert Base.metadata.create_all was called.
        mock_base.metadata.create_all.assert_called_once_with(bind=mocker.ANY)

        # Assert get_user_by_username was called.
        mock_get_user_by_username.assert_called_once_with(mock_session, "admin")

        # Assert hash_password was called.
        mock_hash_password.assert_called_once_with("admin_password")

        # Assert create_user was called.
        mock_create_user.assert_called_once_with(
            mock_session, "admin", mock_hash_password.return_value, "admin"
        )

        # Assert session.rollback was called.
        mock_session.rollback.assert_called_once()

        # Assert session.close was called.
        mock_session.close.assert_called_once()

    # Test that init_db handles errors during Base.metadata.create_all.
    def test_init_db_error_handling_during_create_all(self, mocker):

        # This test does not use the full mock_db_dependencies fixture because
        # it specifically focuses on an error before the session is typically used.
        mock_base = mocker.patch("src.database.init_db.Base")
        mock_session_local = mocker.patch("src.database.init_db.SessionLocal")

        # Simulate an exception during create_all
        mock_base.metadata.create_all.side_effect = Exception(
            "Database connection issue"
        )

        with pytest.raises(Exception, match="Database connection issue"):
            init_db()

        # Assert Base.metadata.create_all was called
        mock_base.metadata.create_all.assert_called_once_with(bind=mocker.ANY)

        # Ensure that no session was created or used if create_all failed early
        mock_session_local.assert_not_called()
