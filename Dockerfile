FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install UV package manager
RUN pip install uv

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install Python dependencies
RUN uv sync --frozen

# Copy application code
COPY bot/ ./bot/
COPY config/ ./config/
COPY locales/ ./locales/
COPY examples/ ./examples/

# Create non-root user
RUN useradd --create-home --shell /bin/bash botuser
RUN chown -R botuser:botuser /app
USER botuser

# Set Python path
ENV PYTHONPATH=/app

# Default command
CMD ["python", "-m", "bot.main"]