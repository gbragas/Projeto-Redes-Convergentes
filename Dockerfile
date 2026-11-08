
# Use Ubuntu 22.04 as the base image
FROM ubuntu:22.04

# Avoid interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# Install NS-3 build dependencies
RUN apt-get update && apt-get install -y \
    g++ \
    python3 \
    python3-dev \
    python3-pip \
    python3-venv \
    pkg-config \
    sqlite3 \
    cmake \
    ninja-build \
    git \
    tar \
    bzip2 \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Create a Python virtual environment
RUN python3 -m venv /opt/ns3-venv

ENV PATH="/opt/ns3-venv/bin:${PATH}"
ENV Python3_EXECUTABLE="/opt/ns3-venv/bin/python3"

# Install CMake and Cppyy for NS-3
RUN python3 -m pip install --no-cache-dir \
    cmake==3.31.6 \
    cppyy==3.1.2

# Define the working directory
WORKDIR /usr/ns3

# Download and extract NS-3.48
RUN wget https://www.nsnam.org/releases/ns-allinone-3.48.tar.bz2 && \
    tar -xjf ns-allinone-3.48.tar.bz2 && \
    rm ns-allinone-3.48.tar.bz2

# Enter the NS-3.48 directory
WORKDIR /usr/ns3/ns-allinone-3.48/ns-3.48

# Configure and build NS-3 with Python bindings
RUN ./ns3 configure \
    --build-profile=optimized \
    --enable-python-bindings \
    --disable-examples \
    --disable-tests \
    --disable-modules="lorawan;netsimulyzer" && \
    ./ns3 build -j 2

# Create the project directory
RUN mkdir -p scratch/network-qos

# Start a Bash shell by default
CMD ["/bin/bash"]

