FROM debian:bullseye-slim

# Set the working directory in the container
WORKDIR /app

# Install Python and pip
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-pip && \
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

# Copy the source code into the container
COPY src/ ./src/

# # Install required dependencies for PrusaSlicer
# RUN apt-get update && apt-get install -y --no-install-recommends \
#     libgl1-mesa-glx \
#     libgtk-3-0 \
#     libegl1 \
#     libxcursor1 \
#     libxinerama1 \
#     liboctoprint-api-python \
#     wget \
#     && apt-get clean && rm -rf /var/lib/apt/lists/*

# Download and install PrusaSlicer
# RUN wget -q -O prusa-slicer.deb https://cdn.prusa3d.com/downloads/drivers/prusa3d-slicer_2.6.0+linux-amd64_stable.deb \
#     && apt-get update \
#     && apt-get install -y --no-install-recommends ./prusa-slicer.deb \
#     && rm prusa-slicer.deb \
#     && apt-get clean && rm -rf /var/lib/apt/lists/*