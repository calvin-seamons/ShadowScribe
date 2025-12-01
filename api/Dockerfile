# FastAPI Backend Dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install PyTorch (CPU version for smaller image) and transformers for local classifier
RUN pip install --no-cache-dir \
    torch --index-url https://download.pytorch.org/whl/cpu
RUN pip install --no-cache-dir \
    transformers==4.36.0 \
    sentence-transformers \
    safetensors \
    sentencepiece \
    protobuf

# Install FastAPI-specific dependencies
RUN pip install --no-cache-dir \
    fastapi==0.104.1 \
    uvicorn[standard]==0.24.0 \
    websockets==12.0 \
    sqlalchemy[asyncio]==2.0.23 \
    aiomysql==0.2.0 \
    alembic==1.12.1 \
    pydantic==2.5.0 \
    pydantic-settings==2.1.0 \
    numpy \
    scikit-learn \
    cryptography \
    pymysql \
    httpx==0.25.2 \
    dacite==1.8.1 \
    rank_bm25==0.2.2 \
    python-dotenv \
    openai \
    anthropic

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
