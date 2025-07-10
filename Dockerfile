# Use a lightweight Python base image
FROM python:3.11-slim

# Set working directory inside container
WORKDIR /app

# Install system dependencies (optional)
RUN apt-get update && apt-get install -y build-essential

# Copy requirements & install first (better caching)
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copy app source code
COPY app/ ./app/
COPY load_data.py .
COPY .env .
COPY test_data/ ./test_data/
COPY entrypoint.sh /entrypoint.sh

# Make sure logs dir exists inside image (just in case)
RUN mkdir -p /app/logs

# Make entrypoint executable
RUN chmod +x /entrypoint.sh

# Expose the port FastAPI listens on
EXPOSE 8000

# Run the entrypoint
ENTRYPOINT ["/entrypoint.sh"]
