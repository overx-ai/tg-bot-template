FROM python:{{ cookiecutter.python_version }}-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY {{ cookiecutter.project_slug.replace('-', '_') }}/ {{ cookiecutter.project_slug.replace('-', '_') }}/
COPY alembic/ alembic/
COPY alembic.ini .
COPY locales/ locales/

# Create non-root user
RUN useradd -m -u 1000 botuser && chown -R botuser:botuser /app
USER botuser

# Run the bot
CMD ["python", "-m", "{{ cookiecutter.project_slug.replace('-', '_') }}.main"]