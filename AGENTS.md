# GEMINI.md

## Project Overview

This project, named Axon, is a local-first AI agent. It features a Python backend built with FastAPI and a React frontend. The project uses `poetry` for managing Python dependencies and `npm` for the frontend.

The key features of Axon include:

*   A plugin architecture for extending its capabilities.
*   Memory capabilities for storing and retrieving information.
*   Goal tracking and reminder functionalities.
*   A command-line interface (CLI) for interaction.
*   A web-based user interface.
*   Support for Docker Compose for easy setup and deployment.

The architecture includes several components:

*   **Backend:** A FastAPI application that serves the API and WebSocket.
*   **Frontend:** A React application for the user interface.
*   **Plugins:** Python modules that extend the agent's functionality.
*   **Databases:** PostgreSQL, Qdrant, and Redis for data storage.
*   **MCP Servers:** Helper services for various tasks.

## Building and Running

### Using Docker (Recommended)

The easiest way to run the project is by using Docker Compose.

1.  Copy the example environment file: `cp .env.example .env`
2.  Build and start all services: `docker compose up --build`

The frontend will be available at `http://localhost:3000` and the backend at `http://localhost:8000`.

### Manual Setup

#### Backend

1.  Install dependencies: `poetry install`
2.  Run the backend server: `python main.py web`

The backend will be running on `localhost:8000`.

#### Frontend

1.  Navigate to the frontend directory: `cd frontend`
2.  Install dependencies: `npm install`
3.  Start the development server: `npm run dev`

The frontend will be running on `localhost:5173`.

### Testing

The project uses `pytest` for backend testing and `tsc` and `eslint` for the frontend.

*   **Run all tests (via pre-commit hooks):** `pre-commit run --all-files`
*   **Run backend tests:** `pytest`
*   **Run frontend type checking:** `cd frontend && npm run type-check`
*   **Run frontend linting:** `cd frontend && npm run lint`

## Development Conventions

*   **Pre-commit Hooks:** The project uses pre-commit hooks to enforce code quality. Install them with `pre-commit install`.
*   **Commit Messages:** Commit messages must follow a specific format, which is enforced by a `commit-msg` git hook.
*   **Plugins:** New plugins can be added by creating a Python file in the `plugins/` directory. Each plugin should have a corresponding `.yaml` file for its manifest.
*   **Configuration:** The application is configured through `config/settings.yaml`. An example is provided in `config/settings.example.yaml`.
