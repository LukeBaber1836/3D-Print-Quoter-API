FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

# Install Python and pip
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-pip git && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Copy the entire working directory into the container
COPY . /app

# Install the Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Download and install PrusaSlicer
RUN apt-get update && apt-get install prusa-slicer -y

# Install locales and configure them
RUN apt-get update && apt-get install -y --no-install-recommends locales && \
    echo "en_US.UTF-8 UTF-8" > /etc/locale.gen && \
    locale-gen && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Set the default locale environment variables
ENV LANG=en_US.UTF-8 \
    LANGUAGE=en_US:en \
    LC_ALL=en_US.UTF-8

# Fly.io doesn't use docker compose, so we need to expose the port manually here
# Expose port 8080
EXPOSE 8080

# Set the command to run the FastAPI app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]