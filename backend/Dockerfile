# ---- Builder Stage ----
# This stage installs dependencies into a virtual environment
FROM python:3.11-slim as builder

WORKDIR /app

# Install poetry
RUN pip install "poetry>=1.5"

# Configure poetry to create the virtual env in the project directory
ENV POETRY_VIRTUALENVS_IN_PROJECT=true

# Copy dependency files
COPY pyproject.toml poetry.lock* ./

# Install dependencies, excluding development ones
RUN poetry install --without dev --no-interaction --no-ansi --no-root

# ---- Final Stage ----
# This stage builds the final, lean image
FROM python:3.11-slim

WORKDIR /app

# Copy the virtual environment from the builder stage
COPY --from=builder /app/.venv ./.venv

# Set the PATH to use the virtual environment
ENV PATH="/app/.venv/bin:$PATH"

# Copy the application source code
COPY . .

# The command to run the application
CMD ["uvicorn", "axon.backend.main:app", "--host", "0.0.0.0", "--port", "8000"]