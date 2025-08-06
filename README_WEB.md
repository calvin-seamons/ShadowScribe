# ShadowScribe Web Application

## Quick Start

### Development Mode

1. **Install Backend Dependencies**
   ```bash
   pip install -r requirements-web.txt
   ```

2. **Start Backend Server**
   ```bash
   cd web_app
   uvicorn main:app --reload --port 8000
   ```

3. **Install Frontend Dependencies**
   ```bash
   cd frontend
   npm install
   ```

4. **Start Frontend Dev Server**
   ```bash
   npm run start
   ```

5. **Access the Application**
   - Frontend: http://localhost:3000
   - API Docs: http://localhost:8000/docs

### Production Mode with Docker

1. **Build and Run with Docker Compose**
   ```bash
   docker-compose up --build
   ```

2. **Access the Application**
   - http://localhost:8000

## Environment Variables

Create a `.env` file in the root directory:

