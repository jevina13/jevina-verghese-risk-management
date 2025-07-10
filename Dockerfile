# Use a lightweight Python base image
FROM python:3.11-slim

# Set working directory inside container
WORKDIR /app

# Install system dependencies if needed
RUN apt-get update && apt-get install -y build-essential

# Copy requirements first and install them
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY app/ ./app/
COPY load_data.py .
COPY .env .
COPY test_data/ ./test_data/

# Copy entrypoint script (from project root) into container
COPY entrypoint.sh /entrypoint.sh

# Make entrypoint executable
RUN chmod +x /entrypoint.sh

# Expose port for FastAPI
EXPOSE 8000

# Set entrypoint
ENTRYPOINT ["/entrypoint.sh"]
