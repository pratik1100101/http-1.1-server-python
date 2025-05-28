import socket
import threading
from typing import Any, Callable, Tuple, Dict, Optional
import os

from router import Router


class Request:
    def __init__(
        self,
        method: str,
        path: str,
        version: str,
        headers: Dict[str, str],
        body_bytes: bytes,
        web_root_dir: str,
        decoded_body: Optional[str] = None,
        params: Optional[Dict[str, str]] = None,
        user: Optional[Dict[str, Any]] = None,
    ) -> None:

        self.method = method
        self.path = path
        self.version = version
        self.headers = headers if headers is not None else {}
        self.body = body_bytes if body_bytes is not None else b""
        self.web_root_dir = web_root_dir
        self.decoded_body = decoded_body
        self.params = params if params is not None else {}
        self.user = user

    def __repr__(self) -> str:
        return f"<Request method={self.method} path={self.path} headers={len(self.headers)} body_len={len(self.body)}>"


class WebServer:
    # Class-level constant for HTTP status lines.
    STATUS_LINES = {
        200: "OK",
        201: "Created",
        204: "No Content",
        301: "Moved Permanently",
        302: "Found",
        400: "Bad Request",
        403: "Forbidden",
        404: "Not Found",
        405: "Method Not Allowed",
        500: "Internal Server Error",
        501: "Not Implemented",  # Useful for methods that are not supported yet.
        # We can add more as needed.
    }

    # Max request size in bytes.
    MAX_BUFFER_SIZE = 1024 * 1024 * 10  # 10 MB

    def __init__(self, host: str, port: str, web_root_dir: str, router: Router) -> None:
        # Initialize the server with the host, port, and web root directory.
        # The host is the IP address or hostname of the server.
        # The port is the port number on which the server will listen for incoming connections.
        # The web root directory is the base directory for serving files.
        # The server socket is created using the socket module.
        # The socket options are set to allow the address to be reused.
        self.host = host
        self.port = int(port)
        self.web_root_dir = web_root_dir
        if not os.path.isdir(self.web_root_dir):
            raise ValueError(
                f"Web root directory '{web_root_dir}' does not exist or is not a directory"
            )
        self.router = router
        self.middleware_functions = []

    def add_middleware(self, middleware_func: Callable) -> None:
        # Adds a middleware function to the server.
        # Middleware functions are called before the main request handler.

        self.middleware_functions.append(middleware_func)
        print(f"Middleware added: {middleware_func.__name__}")

    def start(self) -> None:
        # Create the socket object that the client will connect to.
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Set server socket to allow reusing the address.
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # Binds the server socket to the host and port.
        server_socket.bind((self.host, self.port))
        # The backlog is set to 128, which is the maximum number of queued connections.
        server_socket.listen(128)
        print(f"Server started at http://{self.host}:{self.port}")

        try:
            while True:
                # Accept incoming connections.
                # The accept method blocks until a connection is made.
                client_socket, client_address = server_socket.accept()
                print(f"Accepted connection from {client_address}")

                # We are using threading here to avoid blocking or synchronous behavior.
                # Each client connection will be handled in a separate thread.
                # This allows multiple clients to connect to the server at the same time.
                client_handler = threading.Thread(
                    target=self.handle_client,
                    args=(client_socket, client_address),
                    daemon=True,
                )
                client_handler.start()
                # A daemon thread is a background thread that does not prevent the main program from exiting.
                # You want the server to shut down when the main program is told to,
                # without waiting for every single client connection to wrap up.
        except KeyboardInterrupt:
            # Handles Ctrl+C shut down the server.
            print("\nServer shutting down.")
        finally:
            # Ensure the server socket is closed when the program exits.
            server_socket.close()
            print("Server socket closed.")

    def handle_client(
        self, client_sock: socket.socket, client_addr: Tuple[str, int]
    ) -> None:
        #### NEED TO REDIFINE/COMMENT THIS ####

        # Buffer specific to this client connection
        client_buffer = b""
        # The timeout is a safeguard. It protects your server from hanging indefinitely
        #  on misbehaving or slow clients.
        client_sock.settimeout(10.0)

        try:
            # Loop to handle multiple requests on a persistent connection
            while True:
                # This receives the client's complete request
                parsed_components, consumed_bytes = self.parse_request_from_buffer(
                    client_buffer
                )

                if parsed_components:
                    # If we enter here, we have a request that was successfully parsed
                    # Hence we remove consumed bytes from buffer
                    client_buffer = client_buffer[consumed_bytes:]

                    request = Request(
                        method=parsed_components["method"],
                        path=parsed_components["path"],
                        version=parsed_components["version"],
                        headers=parsed_components["headers"],
                        body_bytes=parsed_components["body_bytes"],
                        web_root_dir=self.web_root_dir,
                        decoded_body=parsed_components["decoded_body"],
                        params=parsed_components.get("params"),
                    )

                    # Checks if the requested path exists as a route in the app.
                    handler_tuple = self.router.resolve_route(
                        request.method, request.path
                    )

                    if handler_tuple:
                        # Since .resolve_route() will return a (handler_function, handler_args) tuple
                        final_handler, handler_args = handler_tuple
                    else:
                        # Returns if the a route is not found for the specific method and path.
                        self.send_response(
                            client_sock,
                            404,
                            "text/plain",
                            b"404 Not Found: Path not found.",
                        )
                        break

                    # Here we create the nested function from the middleware1(middleware2(...(handler))).
                    # What it essentially does is build a chain of function inside a function inside a function...
                    # Yes, yes I know this is an inception reference!
                    # But we are applying the same logic as the movie by nesting the handler function.
                    # The handler is first resolved since it is the innermost function and we get the content
                    # that bubbles up through all the middleware functions and
                    # only then do we get the status, content_type and content that we return at the end
                    wrapper_handler = final_handler
                    for middleware in reversed(self.middleware_functions):
                        wrapper_handler = middleware(wrapper_handler)

                    try:
                        # We call all the nested functions and pass the handler_args as arbitrary keyword args
                        response_status, response_content_type, response_content = (
                            wrapper_handler(request, **handler_args)
                        )
                        # Sends the response depending on what the nested function returns.
                        self.send_response(
                            client_sock,
                            response_status,
                            response_content_type,
                            response_content,
                        )
                    except TypeError as te:
                        # Catches cases where handler args don't match.
                        print(f"Handler argument mismatch for {request.path}: {te}")
                        self.send_response(
                            client_sock,
                            500,
                            "text/plain",
                            b"500 Internal Server Error: Handler signature mismatch.",
                        )
                        break
                    except Exception as e:
                        # Catches all other exceptions.
                        print(f"Error executing handler for {request.path}: {e}")
                        self.send_response(
                            client_sock,
                            500,
                            "text/plain",
                            b"500 Internal Server Error: Handler error.",
                        )
                        break
                    continue
                else:
                    # There might be a case where there is an incomplete request in buffer.
                    # Hence we need to read more from the socket.
                    data = client_sock.recv(4096)
                    if not data:
                        # Client might have disconnected, so we break loop
                        print(f"Client {client_addr} disconnected.")
                        break

                    client_buffer += data

                    # Check for maximum buffer size to prevent memory exhaustion from malicious/bad clients
                    if len(client_buffer) > self.MAX_BUFFER_SIZE:
                        print(f"Buffer overflow for {client_addr}. Closing connection.")
                        self.send_response(
                            client_sock,
                            413,
                            "text/plain",
                            b"413 Payload Too Large: Request or buffered data exceeds limit.",
                        )
                        break

        except socket.timeout:
            print(f"Connection timeout for {client_addr}. Closing.")
        except ValueError as e:
            # Catch parsing errors or invalid request formats.
            print(f"Bad Request Error for {client_addr}: {e}")
            self.send_response(client_sock, 400, "text/plain", str(e).encode("utf-8"))
        except Exception as e:
            # Catch any other unexpected errors during request processing.
            print(f"Internal Server Error for {client_addr}: {e}")
            self.send_response(
                client_sock, 500, "text/plain", b"500 Internal Server Error."
            )
        finally:
            # Ensure the client socket is closed.
            print(f"Connection closed for {client_sock.getpeername()}")
            client_sock.close()

    def parse_request_from_buffer(
        self, buffer: bytes
    ) -> Tuple[Optional[Dict[str, Any]], int]:

        # Find the end of the headers section (double CRLF)
        header_end_index = buffer.find(b"\r\n\r\n")

        if header_end_index == -1:
            # Headers not fully received yet
            return None, 0

        # Extract header bytes (including the double CRLF)
        header_section_bytes = buffer[: header_end_index + 4]

        try:
            # Decode the bytes to a string.
            header_string = header_section_bytes.decode("utf-8")

            print(
                f"--- Request received ---\n{header_string.strip()}\n--- End of Request ---"
            )

            # Split by CRLF (\r\n) to get individual lines of the request.
            request_lines = header_string.split("\r\n")

            if not request_lines or not request_lines[0]:
                # If the first line is empty, we have a malformed request.
                raise ValueError("400 Bad Request: Empty request line")

            # The first line of the request contains the method, path, and HTTP version.
            first_line_parts = request_lines[0].strip().split(" ")

            if len(first_line_parts) < 3:
                # If there are not enough parts, we have a malformed request.
                raise ValueError("400 Bad Request: Malformed request line")

            # Extract all the components of the first line.
            method = first_line_parts[0].upper()
            path_with_query = first_line_parts[1]
            version = first_line_parts[2]

            # Extract all the other headers.
            headers = {}

            for i, line in enumerate(request_lines[1:]):
                if not line.strip():
                    # This checks for an empty line which signals the end of the headers.
                    break

                if ":" in line:
                    # Identifies the header lines by ":" and splits the string from the 1st ":".
                    header_name, header_val = line.split(":", 1)
                    headers[header_name.strip()] = header_val.strip()
                else:
                    # Malformed header line, could indicate a bad request
                    raise ValueError(
                        f"400 Bad Request: Malformed header line: '{line.strip()}'"
                    )

            # Parsing the request body for POST, PUT, PATCH methods.
            body_bytes = b""
            # Get Content-Length header value, case-insensitive and safe.
            content_length_str = headers.get("Content-Length") or headers.get(
                "content-length"
            )
            content_length = 0

            if content_length_str:
                try:
                    # Converting str to int.
                    content_length = int(content_length_str)
                    if content_length < 0:
                        raise ValueError(
                            "400 Bad Request: Negative Content-Length not allowed."
                        )
                except ValueError:
                    raise ValueError("400 Bad Request: Invalid Content-Length header.")

            # We check if the entire body has been received
            body_start_offset = header_end_index + 4
            if len(buffer) < body_start_offset + content_length:
                # We ask the client to get more data
                return None, 0

            # We read the request body only if the header+body length < buffer.
            body_bytes = buffer[body_start_offset : body_start_offset + content_length]
            # Gives a ending point that we can use in the buffer to seperate requests
            bytes_consumed = body_start_offset + content_length

            # We define "decoded_request_body" outside since there might be requests without any body.
            decoded_body = None
            if body_bytes:
                try:
                    decoded_body = body_bytes.decode("utf-8")
                    print(f"Request Body: {decoded_body}")
                except UnicodeDecodeError:
                    # If body cannot be decoded as UTF-8, leave as None since it can be other form of data.
                    decoded_body = None

            path = path_with_query
            params: Optional[Dict[str, str]] = None
            if "?" in path_with_query:
                path, query_string = path_with_query.split("?", 1)
                params = dict(param.split("=", 1) for param in query_string.split("&"))

            return {
                "method": method,
                "path": path,
                "version": version,
                "headers": headers,
                "body_bytes": body_bytes,
                "decoded_body": decoded_body,
                "params": params,
            }, bytes_consumed

        except ValueError as e:
            # Catch specific parsing syntax errors and re-raise them as bad requests
            raise ValueError(f"400 Bad Request: {e}")
        except Exception as e:
            # Catch any unexpected errors during parsing (e.g., list index out of bounds)
            raise ValueError(f"500 Internal Server Error during parsing: {e}")

    def send_response(
        self,
        client_sock: socket.socket,
        status_code: int,
        content_type: str,
        content: bytes,
    ) -> None:
        # Logic to build and send the HTTP response.

        # We look up the status code message in the STATUS_LINE dict in the class.
        status_message = self.STATUS_LINES.get(status_code, "Unknown Status")

        # Here we create the first line of response
        response_line = f"HTTP/1.1 {status_code} {status_message}\r\n"

        # Next we make the headers in form of a dict so that it is easy to handle.
        # The connection is set to keep-alive for success, close for errors
        headers = {
            "Content-Type": content_type,
            "Content-Length": len(content),
            "Connection": "keep-alive" if status_code == 200 else "close",
        }
        # Combine the headers and make it into a str.
        header_lines = ""
        for name, value in headers.items():
            header_lines += f"{name}: {value}\r\n"

        # Add an empty line to signal the end of the header.
        header_lines += "\r\n"

        # Combine the first line, headers and content, while we encode it.
        full_response_bytes = (
            response_line.encode("utf-8") + header_lines.encode("utf-8") + content
        )

        try:
            # Sending the response to the client.
            client_sock.sendall(full_response_bytes)
            print(
                f"Sent response with status {status_code} and {len(content)} bytes of content to {client_sock.getpeername()}"
            )
        except Exception as e:
            # Catches any unknown errors.
            print(f"Error sending response to {client_sock.getpeername()}: {e}")
