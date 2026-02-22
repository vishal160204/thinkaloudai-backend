# Minimal sandbox image for running user code
FROM python:3.13-slim AS python-sandbox

# No network, no root, no extras
RUN useradd -m -s /bin/bash sandbox
RUN apt-get update && apt-get install -y --no-install-recommends \
    nodejs \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Working directory for user code
WORKDIR /code
USER sandbox

# No entrypoint — we pass commands at runtime
