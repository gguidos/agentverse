# Microservice Boilerplate with FastAPI, MongoDB, and Dependency Injection

Welcome to the Microservice Boilerplate repository! This project is a robust and modular backend service built using **FastAPI**, **MongoDB**, and **Dependency Injector**. It is designed to help you quickly get started with building microservices by providing a well-structured and extendable codebase.

## Table of Contents
- [Features](#features)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Environment Setup](#environment-setup)
- [Running the Application](#running-the-application)
  - [Local Development](#local-development)
  - [Using Docker](#using-docker)
- [Endpoints](#endpoints)
- [Testing](#testing)
- [Security and Rate Limiting](#security-and-rate-limiting)
- [Metrics, Monitoring, and Health Checks](#metrics-monitoring-and-health-checks)
- [Contributing](#contributing)
- [License](#license)

## Features

- **FastAPI** framework for creating performant APIs.
- **MongoDB** integration using `motor` for asynchronous operations.
- **Dependency Injection** with `dependency-injector` for modular and maintainable code.
- **Request/Response Validation** using Pydantic models.
- **Custom Middleware** for request tracking (e.g., Request ID).
- **Unified Logging** configuration with support for JSON and file-based logging.
- **Input Sanitization** for preventing XSS and SQL Injection attacks.
- **Global Exception Handling** with a standardized error response format.
- **Rate Limiting** to prevent abuse of the endpoints.
- **Security Headers** such as `Strict-Transport-Security` and `Content-Security-Policy`.
- **API Key Management** for securing the service.
- **Health Checks and Readiness Probes**.
- **Metrics and Monitoring** with Prometheus.
- **Structured Project Layout** following the Clean Architecture principles.
- **Dynamic Configuration** using environment variables with `dotenv`.

## Project Structure

```bash
.
├── Dockerfile
├── README.md
├── docker-compose.yml
├── logs
│   ├── application.log
│   └── errors.log
├── post.http
├── requirements.txt
├── src
│   ├── core
│   │   ├── entities
│   │   │   ├── base_entity.py
│   │   │   └── user.py
│   │   ├── repositories
│   │   │   └── user_repository.py
│   │   ├── schemas
│   │   │   └── user_schema.py
│   │   └── use_cases
│   │       ├── create_user.py
│   │       ├── get_all_users.py
│   │       └── get_user.py
│   ├── dependencies
│   │   ├── api_key_dependency.py
│   │   ├── request_id_dependency.py
│   │   └── user_service_dependency.py
│   ├── infrastructure
│   │   ├── db
│   │   │   └── mongo_client.py
│   │   ├── di_container.py
│   │   ├── exception_handlers.py
│   │   └── logging
│   │       └── logging_config.py
│   ├── interfaces
│   │   └── api
│   │       └── v1
│   │           ├── health_check.py
│   │           └── user_controller.py
│   ├── main.py
│   ├── middleware
│   │   ├── logging_middleware.py
│   │   ├── request_id_middleware.py
│   │   ├── response_interceptor.py
│   │   └── security_headers.py
│   └── services
│       └── user_service.py
└── structure.txt

17 directories, 30 files
```

## Getting Started

### Prerequisites

Make sure you have the following installed on your system:

- Python 3.8 or higher
- MongoDB 4.0 or higher
- Docker (optional, for running via Docker)

### Installation

1. **Clone the repository:**

    ```bash
    git clone https://github.com/your-username/your-repo-name.git
    cd your-repo-name
    ```

2. **Create a virtual environment and activate it:**

    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```

3. **Install the dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

4. **Install MongoDB locally** or ensure a remote instance is accessible.

### Environment Setup

1. **Create a `.env` file** in the root of the project and set up the following environment variables:

    ```ini
    MONGO_URI=mongodb://localhost:27017
    DB_NAME=mydatabase
    DB_COLLECTION=users
    LOG_LEVEL=DEBUG
    ENVIRONMENT=development
    API_KEY=your-api-key-for-secure-access
    ```

2. **Modify the `.env` file** according to your local or production configurations.

## Running the Application

### Local Development

1. **Start MongoDB server** if running locally:

    ```bash
    mongod
    ```

2. **Run the application:**

    ```bash
    uvicorn main:app --host 0.0.0.0 --port 8000 --reload
    ```

3. The API will be available at `http://127.0.0.1:8000`.

### Using Docker

1. **Build the Docker image:**

    ```bash
    docker build -t my-microservice .
    ```

2. **Run the Docker container:**

    ```bash
    docker run -p 8000:8000 --env-file .env my-microservice
    ```

## Endpoints

Here are some key endpoints provided by this boilerplate:

- `GET /api/v1/users/`: Retrieve all users.
- `POST /api/v1/users/`: Create a new user.
- `GET /api/v1/users/id/{user_id}`: Retrieve a user by ID.
- `GET /api/v1/users/email/{email}`: Retrieve a user by email.
- `GET /internal/metrics`: Prometheus metrics endpoint.
- `GET /api/v1/health`: Health endpoint.
- `GET /api/v1/readiness`: Readiness endpoint.

### Sample Request to Create a User

```json
POST /api/v1/users/
{
  "name": "John Doe",
  "email": "john.doe@example.com",
  "age": 30
}
```

### Response Format
```json
{
  "status": "success",
  "data": { ... },
  "message": "Operation completed successfully."
}
```

## Security and Rate Limiting

- `API Key Management`: An X-API-Key header is used for validating access to secure endpoints. The key is defined in the .env file.

- `Rate Limiting`: Middleware to limit the number of requests a client can make in a defined time window. See rate_limiting_middleware.py.

- `Security Headers`: Content-Security-Policy, Strict-Transport-Security, and X-Content-Type-Options headers are added using the security_config.py.

## Metrics, Monitoring, and Health Checks

- `Prometheus Metrics`: /internal/metrics endpoint provides real-time metrics. See metrics.py.

- `Health Checks`: /api/v1/health endpoint provides application health status.

- `Readiness Checks`: /api/v1/readiness endpoint provides database health status.

- `Monitoring & Alerting`: Use Prometheus and Alertmanager for monitoring and alerting setups.

## Testing
To run the tests, make sure you have pytest installed:

```bash
pytest
```
