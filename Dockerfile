# Use an official Python runtime as a parent image.
# Using a specific version tag (e.g., 3.9-slim) is recommended for reproducibility
# and -slim images are smaller.
FROM python:3.10-slim

# Set the working directory in the container.
# All subsequent commands (COPY, RUN, CMD) will be executed in this directory.
WORKDIR /app

# Create a non-root user and group for better security.
# Running containers as a non-root user is a security best practice.
RUN groupadd -r appgroup && useradd --no-log-init -r -g appgroup appuser

# Copy the dependencies file first.
# If your agent has dependencies (e.g., Python packages listed in requirements.txt),
# copy this file and install dependencies before copying the rest of your code.
# This leverages Docker's layer caching: if requirements.txt doesn't change,
# this layer won't be rebuilt, speeding up subsequent builds when only code changes.
COPY requirements.txt .

# Install any needed packages specified in requirements.txt.
# --no-cache-dir reduces image size by not storing the pip cache.
# Ensure you have a requirements.txt file in the same directory as your Dockerfile.
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application's code into the container's /app directory.
# The first '.' refers to the build context (current directory on your host machine),
# and the second '.' refers to the WORKDIR in the container (/app).
COPY . .

# Change ownership of the app directory to the non-root user.
# This ensures the application files are owned by the user running the process.
RUN chown -R appuser:appgroup /app

# Switch to the non-root user.
# Subsequent commands will be run as 'appuser'.
USER appuser

# Define environment variables if your agent needs them.
# Uncomment and modify as needed.
# ENV MY_AGENT_SETTING="some_value"
# ENV ANOTHER_VARIABLE="another_value"

# Expose a port if your agent listens on one (e.g., for a web API or service).
# This is documentation; you still need to map the port when running the container.
# Uncomment and change the port number as needed.
# EXPOSE 8080

# Define the command to run your agent when the container starts.
# Replace 'your_agent_script.py' with the actual main script or command for your agent.
# This is the default command and can be overridden when running the container.
CMD ["python", "main.py"]