# Deployment Guide

## Docker Deployment (Recommended)

The application is fully containerized.

### Prerequisites
- Docker Engine & Docker Compose
- Valid `.env` file

### Steps

1. **Build and Start**
   ```bash
   docker-compose up -d --build
   ```

2. **Verify Status**
   ```bash
   docker-compose ps
   ```

3. **View Logs**
   ```bash
   docker-compose logs -f
   ```

### Configuration

- **Ports**:
  - Frontend: 80
  - Backend: 8000
  - Redis: 6379

- **Environment Variables**:
  Ensure `REDIS_URL` is set to `redis://redis:6379/0` in `.env` when running with Docker Compose (the service name `redis` resolves automatically).

## Manual Deployment

If you cannot use Docker:

1. **Install Redis**: Ensure Redis is running locally on port 6379.
2. **Backend**:
   ```bash
   pip install -r requirements.txt
   ./start_prod.sh
   ```
3. **Frontend**:
   ```bash
   cd web-portal
   npm run build
   # Serve the 'dist' folder using nginx or serve
   npx serve -s dist
   ```
