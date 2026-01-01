# Root Dockerfile for Cloud Run "Deploy from repository"
#
# Cloud Build looks for Dockerfile at repo root by default.
# This builds the backend from services/echo_backend/ with repo-root context.
#
# For local builds from services/echo_backend/, use that directory's Dockerfile.

FROM python:3.11 AS builder

ENV PATH="/opt/venv/bin:$PATH"
RUN python -m venv /opt/venv

# Install build dependencies for liblc3
RUN apt-get update && apt-get install -y \
    git \
    gcc \
    g++ \
    meson \
    ninja-build \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Build liblc3 and create wheel
WORKDIR /tmp
RUN git clone https://github.com/google/liblc3.git && \
    cd liblc3 && \
    meson setup build && \
    cd build && \
    meson install && \
    ldconfig && \
    cd /tmp/liblc3 && \
    python3 -m pip wheel --no-cache-dir --wheel-dir /tmp/wheels .

# Install Python requirements (path adjusted for repo root context)
WORKDIR /opt/venv
COPY services/echo_backend/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /tmp/requirements.txt

# --- Runtime stage ---
FROM python:3.11-slim

WORKDIR /app
ENV PATH="/opt/venv/bin:$PATH"
ENV LD_LIBRARY_PATH=/usr/local/lib:$LD_LIBRARY_PATH

RUN apt-get update && apt-get -y install ffmpeg curl unzip && rm -rf /var/lib/apt/lists/*

# Copy compiled liblc3 library and wheel from builder
COPY --from=builder /usr/local/lib/liblc3.so* /usr/local/lib/
COPY --from=builder /tmp/wheels /tmp/wheels

# Install liblc3 Python package and set library path
RUN ldconfig && \
    pip install --no-cache-dir /tmp/wheels/*.whl && \
    rm -rf /tmp/wheels

COPY --from=builder /opt/venv /opt/venv

# Copy backend source (path adjusted for repo root context)
COPY services/echo_backend/ .

# Create non-root user for security
RUN groupadd --gid 1000 appuser && \
    useradd --uid 1000 --gid 1000 --no-create-home appuser && \
    chown -R appuser:appuser /app /opt/venv
USER appuser

# Cloud Run sets PORT env var; default to 8080 for compatibility
ENV PORT=8080
EXPOSE 8080

# Bind to 0.0.0.0 (required for Cloud Run) and use PORT from environment
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080}
