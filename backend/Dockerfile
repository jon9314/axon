# ---- Builder Stage ----
# This stage installs dependencies into a virtual environment
FROM python:3.11-slim as builder

WORKDIR /app

# Install system dependencies for psycopg2
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install poetry
RUN pip install "poetry>=1.5"

# Configure poetry to create the virtual env in the project directory
ENV POETRY_VIRTUALENVS_IN_PROJECT=true

# Copy dependency files
COPY pyproject.toml poetry.lock* ./

# Install dependencies, excluding development ones
RUN poetry install --without dev --no-interaction --no-ansi --no-root

# Install optional dependencies (postgres, vector, calendar, notify)
RUN .venv/bin/pip install psycopg2-binary qdrant-client icalendar plyer

# ---- Final Stage ----
# This stage builds the final, lean image
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies for psycopg2
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copy the virtual environment from the builder stage
COPY --from=builder /app/.venv ./.venv

# Set the PATH to use the virtual environment
ENV PATH="/app/.venv/bin:$PATH"

# Copy the application source code
COPY . .

# The command to run the application
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]