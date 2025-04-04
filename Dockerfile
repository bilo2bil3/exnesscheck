FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn psycopg2-binary

# Copy project
COPY . .

# Collect static files
RUN python manage.py collectstatic --noinput

# Set the default port for DigitalOcean App Platform
ENV PORT=8080

# Set the application module
ENV GUNICORN_CMD_ARGS="--worker-tmp-dir /dev/shm"

# Expose port
EXPOSE 8080

# Run gunicorn
CMD gunicorn exness_client_validator.wsgi:application --bind 0.0.0.0:8080 