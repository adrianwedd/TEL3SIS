# Start with a slim, secure Python base image
FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app

# Install system dependencies that may be required by Python packages
# e.g., for cryptography or other compiled libraries
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file first to leverage Docker layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY . .

# Placeholder command to keep the container running for development
# This will be replaced by the actual application command (e.g., gunicorn, flask)
CMD ["sleep", "infinity"]
