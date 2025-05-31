# HTTP/1.1 Server in Python

A custom HTTP/1.1 server implementation built from scratch in Python, demonstrating fundamental web server concepts and modern authentication patterns.

## Features

### Core HTTP/1.1 Implementation
- **Raw Socket Programming**: Built from scratch using Python's `socket` library, bypassing high-level frameworks
- **HTTP Protocol Parsing**: Custom implementation of HTTP request/response parsing and formatting
- **Persistent Connections (Keep-Alive)**: Maintains connections for multiple requests to reduce overhead
- **HTTP Methods**: GET and POST support with extensible architecture for additional methods
- **Static File Serving**: Efficient serving of HTML, CSS, JavaScript, and other static assets
- **Content-Type Detection**: Automatic MIME type detection based on file extensions
- **Threading Model**: Multi-threaded request handling for concurrent client connections

### Security & Authentication
- **JWT Authentication**: Stateless token-based authentication with configurable expiration
- **Password Security**: Secure password hashing and validation
- **Protected Routes**: Decorator-based route protection (`@protected_route`)
- **User Management**: Complete user registration and authentication flow
- **CORS Handling**: Cross-origin request support for API endpoints

### Architecture & Design Patterns
- **Modular Design**: Clean separation of concerns across multiple modules
- **Repository Pattern**: Database abstraction layer for user management
- **Middleware Pipeline**: Extensible request/response processing chain
- **Dynamic Routing**: JSON-configurable routes with automatic loading and URL pattern matching
- **Database Integration**: PostgreSQL support with connection pooling considerations
- **Configuration Management**: Environment-based configuration with sensible defaults

### Testing
- **Unit Testing**: This project maintains **88% test coverage** across all major components with a comprehensive unit test suite.

## 📊 Project Status

- ✅ Core HTTP/1.1 server implementation
- ✅ Dynamic routing with JSON configuration
- ✅ Database integration with repository pattern
- ✅ JWT authentication system
- ✅ Middleware pipeline
- ✅ Static file serving
- ✅ Comprehensive unit testing (88% coverage)
- 🔄 Complete unit testing (95%+ coverage) (planned)
- 🔄 Integration testing (planned)
- 🔄 Additional HTTP Methods (planned)
- 📝 File Upload Support
- 📝 Basic Caching
- 📝 Containerization

## 📁 Project Structure

```
.
├── src/
│   ├── __init__.py
│   ├── webserver.py
│   ├── router.py
│   ├── loader.py
│   ├── decorators.py
│   ├── database/
│   │   ├── __init__.py
│   │   ├── init_db.py
│   │   ├── models.py
│   │   ├── db_config.py
│   │   └── user_repository.py
│   ├── handlers/
│   │   ├── __init__.py
│   │   ├── api_handlers.py
│   │   ├── auth_handlers.py
│   │   └── static_handlers.py
│   ├── middleware/
│   │   ├── __init__.py
│   │   ├── auth_middleware.py
│   │   └── logger.py
│   └── utils/
│       ├── __init__.py
│       └── auth_utils.py
├── server.py
├── .env
├── tests/
│   └── unit
│       ├── test_api_handlers.py
│       ├── test_auth_handlers.py
│       ├── test_decorators.py
│       ├── test_init_db.py
│       ├── test_loader.py
│       ├── test_router.py
│       ├── test_static_handlers.py
│       └── test_webserver.py
├── config/
│   └── routes.json
└── webroot/
    ├── index.html
    ├── script.js
    └── style.css
```

### Test Coverage Breakdown

| Component | Coverage | Status |
|-----------|----------|---------|
| Router | 100% | ✅ Complete |
| Decorators | 100% | ✅ Complete |
| API Handlers | 95% | ✅ Excellent |
| Auth Handlers | 89% | ✅ Very Good |
| Static Handlers | 96% | ✅ Excellent |
| WebServer Core | 84% | ✅ Good |
| Database Init | 92% | ✅ Excellent |
| Route Loader | 83% | ✅ Good |
| **Overall** | **88%** | ✅ **Excellent** |

### Running Tests

Execute the full test suite with detailed coverage report:
```bash
python -m pytest
```

Run specific test modules:
```bash
python -m pytest tests/unit/test_webserver.py -v
python -m pytest tests/unit/test_auth_handlers.py -v
python -m pytest tests/unit/test_api_handlers.py -v
```

## 🛠️ Installation

### Prerequisites
- Python 3.12.6
- PostgreSQL database

### Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/pratik1100101/http-1.1-server-python.git
   cd http-1.1-server-python
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**
   
   Create a `.env` file with the following variables:
   ```env
   HOST=localhost
   PORT=8080
   JWT_SECRET_KEY=your-secret-key-here
   WEB_ROOT_DIR=webroot
   ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=30
   DATABASE_URL=postgresql://username:password@localhost/dbname
   ```

4. **Initialize database**
   ```bash
   python database/init_db.py
   ```

5. **Run the server**
   ```bash
   python server.py
   ```

## 🌐 API Endpoints

### Static Routes
- `GET /` - Serves the main HTML page
- `GET /style.css` - CSS stylesheet
- `GET /script.js` - JavaScript file

### Authentication
- `POST /api/register` - User registration
- `POST /api/login` - User login (returns JWT token)

### API Routes
- `GET /api/data` - Public data endpoint
- `POST /api/data` - Public data submission
- `GET /api/profile` - Protected user profile (requires JWT)
- `GET /api/protected_data` - Protected sample data (requires JWT)

### Authentication Usage

For protected routes, include the JWT token in the Authorization header:
```bash
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" http://localhost:8080/api/profile
```

## ⚙️ Configuration

### Environment Variables (.env)
- `HOST`: Server host address
- `PORT`: Server port number
- `JWT_SECRET_KEY`: Secret key for JWT token signing
- `WEB_ROOT_DIR`: Directory for static files
- `ALGORITHM`: JWT signing algorithm
- `ACCESS_TOKEN_EXPIRE_MINUTES`: Token expiration time
- `DATABASE_URL`: PostgreSQL connection string

## 🔧 Technical Implementation Details

### HTTP/1.1 Protocol Features
- **Persistent Connections**: Implements `Connection: keep-alive` for connection reuse
- **HTTP Headers**: Full header parsing and custom header support
- **Status Codes**: Comprehensive HTTP status code responses (200, 404, 401, 500, etc.)
- **Content Negotiation**: MIME type detection and appropriate Content-Type headers
- **Request Methods**: GET and POST with extensible framework for additional methods

### Threading and Concurrency
- **Thread-per-Request**: Each client connection handled in separate thread
- **Socket Management**: Proper socket cleanup and resource management
- **Concurrent Requests**: Multiple simultaneous client connections supported
- **Thread Safety**: Shared resources protected with appropriate synchronization

### Database Integration
- **PostgreSQL Adapter**: Native PostgreSQL connectivity
- **Connection Pooling Ready**: Architecture supports connection pooling implementation
- **Query Abstraction**: Repository pattern abstracts SQL queries
- **Migration Support**: Database schema initialization and versioning

### JWT Implementation
- **Token Structure**: Standard JWT format with header, payload, and signature
- **Configurable Algorithms**: Support for different signing algorithms (HS256 default)
- **Expiration Handling**: Configurable token expiration with validation
- **Secure Storage**: Client-side token storage recommendations

### Configuration System
- **Environment Variables**: Twelve-factor app methodology compliance
- **Route Configuration**: JSON-based route definitions for easy modification
- **Development/Production**: Environment-specific configuration support
- **Secrets Management**: Secure handling of sensitive configuration data

## 🏗️ Architecture Overview

### Low-Level HTTP Implementation
This server implements HTTP/1.1 from the ground up using raw TCP sockets, providing insight into:
- **Socket Programming**: Direct TCP socket manipulation for network communication
- **HTTP Protocol**: Manual parsing of HTTP headers, methods, and body content
- **Request Lifecycle**: Complete request/response cycle handling
- **Connection Management**: Keep-alive connections and proper socket cleanup

### Core Components

#### WebServer (`webserver.py`)
- **Socket Management**: Creates and manages TCP server socket
- **Threading**: Spawns new threads for each client connection
- **HTTP Parsing**: Parses raw HTTP requests into structured data
- **Response Formatting**: Formats responses according to HTTP/1.1 specification
- **Keep-Alive**: Implements persistent connection handling

#### Router (`router.py`)
- **URL Matching**: Exact path matching with query parameter extraction
- **Handler Dispatch**: Routes requests to appropriate handler functions
- **Method Filtering**: Ensures handlers only receive supported HTTP methods
- **Middleware Integration**: Applies middleware chain before handler execution

#### Middleware System
- **Request Pipeline**: Pre-processing of incoming requests
- **Authentication**: JWT token validation and user context injection
- **Logging**: Request/response logging with configurable detail levels
- **Error Handling**: Centralized error processing and response formatting

#### Database Layer
- **Connection Management**: PostgreSQL connection handling
- **Repository Pattern**: Abstracted data access layer
- **User Management**: Complete user CRUD operations
- **Schema Management**: Database initialization and migration support

### Request Flow
1. **Socket Accept**: Server accepts incoming TCP connection
2. **HTTP Parsing**: Raw request data parsed into HTTP components
3. **Routing**: URL matched against configured routes
4. **Middleware**: Authentication and logging middleware applied
5. **Handler Execution**: Business logic executed in appropriate handler
6. **Response**: HTTP response formatted and sent back to client
7. **Connection**: Keep-alive or connection closure based on headers

### Security Model
- **Stateless Authentication**: JWT tokens eliminate server-side session storage
- **Token Validation**: Cryptographic signature verification for all protected routes
- **Password Security**: Industry-standard password hashing with salt
- **Route Protection**: Granular access control at the endpoint level

## 🚧 Current Limitations & Future Enhancements

This is an educational/proof-of-concept implementation with the following limitations:

### HTTP Protocol Limitations
- **Method Support**: Limited to GET and POST (PUT, DELETE, PATCH, OPTIONS not implemented)
- **Transfer Encoding**: No chunked transfer encoding support
- **Content Compression**: No gzip/deflate compression
- **HTTP Pipelining**: Sequential request processing only
- **Range Requests**: No partial content support for large files
- **Caching**: No HTTP caching headers or conditional requests

### Security Limitations
- **Transport Security**: HTTP only (no HTTPS/TLS encryption)
- **Input Validation**: Basic validation, could be more comprehensive
- **Rate Limiting**: No built-in DDoS or abuse protection
- **CSRF Protection**: No cross-site request forgery prevention
- **Security Headers**: Missing security-focused HTTP headers

### Performance & Scalability
- **Threading Model**: Thread-per-request (not async I/O)
- **Connection Pooling**: Database connections not pooled
- **Memory Management**: No built-in memory usage optimization
- **Static File Caching**: Files read from disk on each request
- **Load Balancing**: Single-instance deployment only

### Feature Gaps
- **WebSocket Support**: No real-time communication capabilities
- **File Upload**: No multipart/form-data handling
- **Session Management**: Only stateless JWT (no server-side sessions)
- **Content Negotiation**: Limited MIME type support
- **Internationalization**: No i18n/l10n support

### Potential Improvements
- **Async Implementation**: Migrate to `asyncio` for better concurrency
- **HTTPS Support**: Add TLS/SSL encryption capabilities
- **Advanced Routing**: Regular expressions and path parameters
- **Monitoring**: Add metrics collection and health check endpoints
- **Containerization**: Docker support for easy deployment
- **Testing**: Comprehensive integration test suite

## 🎯 Learning Objectives & Educational Value

This project serves as a comprehensive educational resource for understanding:

### Web Server Fundamentals
- **Network Programming**: TCP socket programming and network communication
- **HTTP Protocol**: Deep dive into HTTP/1.1 specification and implementation
- **Request/Response Cycle**: Complete understanding of web request processing
- **Connection Management**: Socket lifecycle and resource management

### Software Architecture Patterns
- **Modular Design**: Separation of concerns and clean code architecture
- **Repository Pattern**: Database abstraction and data access layers
- **Middleware Pattern**: Request/response processing pipelines
- **Decorator Pattern**: Cross-cutting concerns like authentication
- **Configuration Management**: Environment-based application configuration

### Security Concepts
- **Authentication vs Authorization**: Understanding the difference and implementation
- **JWT Tokens**: Stateless authentication mechanisms
- **Password Security**: Hashing, salting, and secure storage practices
- **Route Protection**: Implementing granular access controls

### Database Integration
- **ORM-less Development**: Direct database interaction without heavy frameworks
- **Connection Management**: Database connectivity and resource optimization
- **SQL Best Practices**: Query optimization and security considerations

### Development Best Practices
- **Error Handling**: Graceful error management and user feedback
- **Logging**: Application monitoring and debugging techniques
- **Testing Strategies**: Unit testing approaches for web applications
- **Documentation**: Code documentation and API specification

## 🔬 Comparison with Production Frameworks

Understanding how this implementation differs from production frameworks:

### vs Flask/Django
- **Lower Level**: Direct socket programming vs framework abstractions
- **Educational Focus**: Transparency over convenience and productivity
- **Manual Implementation**: Everything built from scratch for learning

### vs Node.js/Express
- **Threading Model**: Thread-per-request vs event-loop architecture
- **Language Ecosystem**: Python vs JavaScript ecosystem differences
- **Performance Trade-offs**: Educational clarity vs production optimization

### vs Apache/Nginx
- **Scope**: Application server vs full-featured web server
- **Performance**: Single-threaded Python vs optimized C implementations
- **Features**: Basic HTTP vs comprehensive web server capabilities

## 🤝 Contributing & Extension Ideas

This educational project welcomes contributions and experimentation. Here are some suggested enhancements:

### Beginner Enhancements
- **Additional HTTP Methods**: Implement PUT, DELETE, PATCH, OPTIONS
- **Better Error Pages**: Custom HTML error pages instead of plain text
- **File Upload Support**: Handle multipart/form-data requests
- **Basic Caching**: Implement simple in-memory caching for static files
- **Configuration Validation**: Add validation for environment variables

### Intermediate Challenges
- **HTTPS Support**: Implement SSL/TLS encryption using Python's `ssl` module
- **Session Management**: Add server-side session storage as alternative to JWT
- **Advanced Routing**: Regular expression patterns and path parameters
- **Request Compression**: Add gzip compression for responses
- **WebSocket Protocol**: Implement basic WebSocket support

### Advanced Projects
- **Async Implementation**: Rewrite using `asyncio` for better performance
- **HTTP/2 Support**: Implement HTTP/2 protocol features
- **Load Balancer**: Create a simple load balancer for multiple server instances
- **Plugin System**: Design an extensible plugin architecture
- **Performance Monitoring**: Add metrics collection and monitoring endpoints

### Code Quality Improvements
- **Integration Tests**: End-to-end testing of API endpoints
- **Code Coverage**: Measure and improve test coverage
- **Documentation**: Auto-generated API documentation

### Contribution Guidelines
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request with detailed description

## 📚 Additional Resources

For deeper understanding of the concepts implemented:

### HTTP Protocol
- [RFC 7230-7237](https://tools.ietf.org/html/rfc7230): HTTP/1.1 Specification
- [MDN HTTP Guide](https://developer.mozilla.org/en-US/docs/Web/HTTP): Comprehensive HTTP documentation
- [HTTP/1.1 vs HTTP/2](https://developers.google.com/web/fundamentals/performance/http2): Protocol comparison

### Socket Programming
- [Python Socket Documentation](https://docs.python.org/3/library/socket.html): Official socket module docs
- [Beej's Guide to Network Programming](https://beej.us/guide/bgnet/): Network programming fundamentals

### Web Security
- [OWASP Top 10](https://owasp.org/www-project-top-ten/): Web application security risks
- [JWT Best Practices](https://auth0.com/blog/a-look-at-the-latest-draft-for-jwt-bcp/): JWT security guidelines

### Software Architecture
- [Clean Architecture](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html): Robert Martin's architecture principles
- [Repository Pattern](https://martinfowler.com/eaaCatalog/repository.html): Data access abstraction

## 📄 License

This project is open source and available for educational purposes.

---

**Note**: This server is intended for learning and development purposes only. It should not be used in production environments without significant security and performance enhancements.