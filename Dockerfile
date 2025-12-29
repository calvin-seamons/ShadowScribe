# Cloud Run Production Dockerfile for ShadowScribe API
# Optimized for faster builds with consolidated dependencies

FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    pkg-config \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy and install ALL Python dependencies in single layer (maximizes cache hits)
COPY requirements-cloudrun.txt .
RUN pip install --no-cache-dir -r requirements-cloudrun.txt

# Pre-download HuggingFace models during build to avoid runtime downloads
# This prevents cold-start timeouts and HuggingFace rate limits
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('BAAI/bge-base-en-v1.5')"

# Copy models and knowledge base (changes rarely - good cache layer)
COPY models/ ./models/
COPY knowledge_base/ ./knowledge_base/

# Copy application code LAST (changes frequently)
COPY api/ ./api/
COPY src/ ./src/

# Cloud Run configuration
ENV PORT=8080
EXPOSE 8080

CMD exec uvicorn api.main:app --host 0.0.0.0 --port ${PORT}
