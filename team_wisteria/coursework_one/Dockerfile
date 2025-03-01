FROM python:3.11-bullseye

# Set environment variables for Poetry installation and configuration
ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    POETRY_VERSION=1.6.1 \
    POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_NO_INTERACTION=1

# Install system dependencies required for Poetry, Ollama, and Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl build-essential libffi-dev libssl-dev && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install poetry

# Install Ollama CLI (assumes Linux-based installation)
RUN curl -sSL https://ollama.com/download/linux | bash && mv ollama /usr/local/bin/

# Create a working directory for the application
WORKDIR /app

# Copy Poetry configuration files first to leverage Docker's caching mechanism
COPY pyproject.toml poetry.lock ./

# Install Python dependencies using Poetry
RUN poetry install --no-dev --no-root
RUN poetry run python -m spacy download en_core_web_sm
RUN poetry run python -m nltk.downloader stopwords


# Copy the rest of the application code into the container
COPY . .

# Expose the port used by Ollama (default: 11434)
EXPOSE 11434

# Set the default command to start a Bash shell (customize as needed)
CMD ["bash"]
