FROM python:3.11-slim as backend

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY src ./src
COPY web_app ./web_app
COPY knowledge_base ./knowledge_base
COPY config.ini .

# Build frontend
FROM node:18-alpine as frontend

WORKDIR /app/frontend

# Install dependencies
COPY frontend/package*.json ./
RUN npm ci

# Copy frontend code
COPY frontend .

# Build frontend
RUN npm run build

# Final image
FROM python:3.11-slim

WORKDIR /app

# Copy from backend stage
COPY --from=backend /app .
COPY --from=backend /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages

# Copy built frontend
COPY --from=frontend /app/frontend/build ./frontend/build

# Expose port
EXPOSE 8000

# Start the server
CMD ["uvicorn", "web_app.main:app", "--host", "0.0.0.0", "--port", "8000"]
