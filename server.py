import os

from dotenv import load_dotenv
from middleware.auth_middleware import auth_middleware
from loader import load_routes, load_users
from webserver import WebServer
from router import Router
from handlers.static_handlers import serve_static_file
from handlers.api_handlers import get_data, post_data
from middleware.logger import logger_middleware

# Important, it ensures we will only have one instance of UserTable
from database.db import user_table

# from database.db_connection import get_db_connection
load_dotenv()
WEB_ROOT_DIR = os.getenv("WEB_ROOT_DIR")
HOST = os.getenv("HOST")
PORT = os.getenv("PORT")
SECRECT_KEY = os.getenv("JWT_SECRET_KEY")


def main():
    # Check if the all .env are set
    if not HOST or not PORT or not WEB_ROOT_DIR:
        print(f"Could not start server as the host or port or web_root_dir is not set.")
        return

    # Initialize the Router.
    router = Router()

    # Initialize the WebServer.
    server = WebServer(HOST, PORT, WEB_ROOT_DIR, router)
    # Add the middleware, order matters here auth first and then logger
    server.add_middleware(auth_middleware)
    server.add_middleware(logger_middleware)
    # Load routes after middleware is added
    # Add here if you are applying the programmatic routing logic and remove load_routes
    load_routes(router)
    load_users(user_table)
    # Establish database connection (if needed)
    # db_connection = get_db_connection()
    # if db_connection:
    # print("Database connection established successfully.")
    # You might pass the db_connection to handlers or store it in the server
    # For simplicity, we'll just print a message here.
    # else:
    # print("Failed to establish database connection.")
    print(f"Starting server on http://{HOST}:{PORT}")
    try:
        # Start server once all checks are done
        server.start()
    except KeyboardInterrupt:
        print("\nShutting down server.")
    # finally:
    # Close database connection if it was opened
    # if db_connection:
    # db_connection.close()
    # print("Database connection closed.")


if __name__ == "__main__":
    main()


# Add this to the comment # Add here... if you are using programmatic routing
##Define the routes using decorators.
##### Static file routes
####@router.route("GET", "/", filepath="index.html", web_root_dir=web_root_dir)
####def index_route_handler(request, **kwargs):
######### This wrapper handler's job is to call the actual serve_static_file handler.
######### It receives `request` and unpacked `handler_args` from the decorator.
########return serve_static_file(request, **kwargs)

####@router.route("GET", "/style.css", filepath="style.css", web_root_dir=web_root_dir)
####def style_route_handler(request, **kwargs):
########return serve_static_file(request, **kwargs)

####@router.route("GET", "/script.js", filepath="script.js", web_root_dir=web_root_dir)
####def script_route_handler(request, **kwargs):
########return serve_static_file(request, **kwargs)

##### API routes
####@router.route("GET", "/api/data")
####def api_get_data_handler(request, **kwargs): # kwargs is present for consistency but not used here
########return get_data(request)

####@router.route("POST", "/api/data")
####def api_post_data_handler(request, **kwargs): # kwargs is present for consistency but not used here
########return post_data(request)
