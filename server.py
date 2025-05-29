import os

from dotenv import load_dotenv
from database.init_db import init_db
from middleware.auth_middleware import auth_middleware
from loader import load_routes
from webserver import WebServer
from router import Router
from handlers.static_handlers import serve_static_file
from handlers.api_handlers import get_data, post_data
from middleware.logger import logger_middleware

# from database.db_connection import get_db_connection
load_dotenv()
WEB_ROOT_DIR = os.getenv("WEB_ROOT_DIR")
HOST = os.getenv("HOST")
PORT = os.getenv("PORT")


def main():
    # Check if the all .env are set
    if not HOST or not PORT or not WEB_ROOT_DIR:
        print(f"Could not start server as the host or port or web_root_dir is not set.")
        return

    print("Initializing database...")
    init_db()
    print("Database initialization complete.")

    # Initialize the Router.
    router = Router()
    load_routes(router)
    print("Routes loaded into router.")

    # Initialize the WebServer.
    server = WebServer(HOST, PORT, WEB_ROOT_DIR, router)
    # Add the middleware, order matters here auth first and then logger
    server.add_middleware(logger_middleware)
    server.add_middleware(auth_middleware)
    # Load routes after middleware is added

    print(f"Starting server on http://{HOST}:{PORT}")
    try:
        # Start server once all checks are done
        server.start()
    except KeyboardInterrupt:
        print("\nShutting down server.")


if __name__ == "__main__":
    main()
