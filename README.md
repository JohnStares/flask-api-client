# Flask API Client - CSRF-Aware Postman Alternative

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

> **A personal project** - An API testing client built specifically to solve the CSRF token injection pain point that Postman doesn't handle automatically.

## 📌 Why I Built This

Postman is great, but it has a frustrating limitation: **it doesn't automatically extract CSRF tokens from cookies and inject them into subsequent requests**. 

### The Problem
When working with Flask APIs (and many other frameworks), you need to:
1. Make a POST request that returns a `csrf_access_token` cookie amongst others (auth endpoint)
2. Manually copy that token
3. Paste it as an `X-CSRF-TOKEN` header for every POST/PUT/DELETE request
4. Repeat every time the token renews

This becomes tedious and error-prone, especially during active development.

### The Solution
This client **automatically**:
- Extracts CSRF tokens from response cookies
- Injects them into the appropriate headers for non-GET requests
- Persists cookies across sessions
- Saves you from manual token management

> **Note**: This is a personal project built for my specific workflow. It's not meant to replace Postman for everyone, but it solves *my* problem perfectly.

## ✨ Features

### Core Functionality
- ✅ **Automatic CSRF Token Management** - Extracts and injects tokens without manual intervention
- ✅ **Cookie Persistence** - Saves cookies to disk, survives application restarts
- ✅ **Session Management** - Uses `requests.Session()` for automatic cookie handling
- ✅ **Request History** - Save and load requests for later use

### HTTP Methods
- GET, POST, PUT, PATCH, DELETE support
- Custom headers editor
- Multiple body types (JSON, Form Data, Raw text)
- Query parameters support

### User Interface
- **Clean tabbed interface** - Separate sections for request, headers, body, and response
- **Syntax highlighting** - JSON formatting for request/response bodies
- **Real-time status** - Request duration and status codes
- **Cookie viewer** - Inspect stored cookies at any time

### Data Persistence
- Save/load requests to JSON files
- Automatic cookie storage between sessions
- Response export functionality

## 🏗️ Architecture (SOLID Principles)

This project follows **SOLID design principles** with clear separation of concerns:

### Design Patterns Used
- **Strategy Pattern** - Pluggable cookie storage backends
- **Facade Pattern** - Simplified `APIClient` interface
- **Dependency Injection** - Components receive dependencies via constructors

## 🚀 Getting Started

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/flask-api-client.git
cd flask-api-client

# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install requests

# From the project root
python3 run.py
```

## 🎨 GUI Credits
GUI Implementation and Design: DeespSeek AI - Built with Python's tkinter library, featuring:

Multi-tab interface for organized workflow

Custom styling for better user experience

Threaded requests to prevent UI freezing

Responsive layout that works on different screen sizes

The GUI was intentionally kept simple and functional. No external UI frameworks were used to minimize dependencies.

## 🤝 Contributing
This is a personal project built for my specific needs. However, if you find it useful and want to contribute:

1. Fork the repository

2. Create a feature branch

3. Submit a pull request

### Areas that could use improvement:

- Add support for other frameworks (Django, Express, etc.)

- Implement request collections

- Add environment variables

- Create dark mode theme

## ❓ FAQ
Q: Why not just use Postman?
A: Postman doesn't automatically inject CSRF tokens from cookies. While you can write JavaScript scripts to do this, I prefer Python and wanted a solution I fully understand and control.

Q: Does this work with non-Flask APIs?
A: It should work with any API that uses cookie-based CSRF tokens. You can configure the cookie and header names in the settings.

Q: Is this production-ready?
A: This is a development tool, not for production use. It's designed for API testing during development.

Q: Can I add authentication headers?
A: Yes! The client automatically extracts Bearer tokens from JSON responses and adds them to subsequent requests.

## 🐛 Known Limitations
Only supports cookie-based CSRF tokens (not header-based)

JSON responses only (for automatic token extraction)

Built and tested primarily on Ubuntu 22.04

No built-in API documentation viewer

## 📝 Release Notes
v1.0.0 (Current)
Initial release

Automatic CSRF token injection

Basic GUI interface

Request save/load functionality

Cookie persistence

## Future Ideas
Dark mode

Request collections

Environment variables

GraphQL support

WebSocket testing


## 📧 Contact
For issues or suggestions, please open a GitHub issue.

Built with ❤️ for developers tired of manually copying CSRF tokens

Remember: This is a personal project that solves my specific problem. It might not be perfect for everyone, but it's perfect for me!

