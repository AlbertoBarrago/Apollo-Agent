# Use a specific Python 3.10 slim image for reproducibility and smaller size.
FROM python:3.10-slim

# Set the application's working directory.
WORKDIR /app

# Create a non-root user and group for enhanced security.
RUN groupadd -r appgroup && useradd --no-log-init -r -g appgroup appuser

# Copy and install dependencies first to leverage Docker layer caching.
# If requirements.txt doesn't change, this layer won't be rebuilt.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code.
COPY . .

# Ensure the application files are owned by the non-root user.
RUN chown -R appuser:appgroup /app

# Switch to the non-root user for running the application.
USER appuser

# Define environment variables if your agent needs them.
# Example:
# ENV MY_AGENT_SETTING="some_value"

# Expose a port if your agent listens on one (e.g., for a web API).
# This is for documentation; port mapping is done during 'docker run' or in docker-compose.
# Example:
# EXPOSE 8080

# Default command to run the application.
CMD ["python", "main.py"]