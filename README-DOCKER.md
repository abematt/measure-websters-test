# Complete Docker Setup Guide for Webster's RAG System

## 🏗️ Architecture Overview

Webster's uses a **containerized microservices architecture** with:

- **Backend Container**: FastAPI server with LlamaIndex (Python 3.11)
- **Frontend Container**: Next.js 15.4 chat interface (Node.js 20)
- **MongoDB**: Runs on host machine (accessed via `host.docker.internal`)
- **Persistent Storage**: Index data stored in Docker volumes

---

## 🚀 Development Setup (Hot Reload)

### Prerequisites
1. **Docker & Docker Compose** installed
2. **MongoDB** running locally on default port `27017`
3. **OpenAI API Key** for embeddings and LLM

### Quick Start

```bash
# 1. Clone and navigate to project
cd /path/to/websters

# 2. Set up environment variables
cp .env.example .env
# Edit .env with your API keys:
# OPENAI_API_KEY=your-openai-key
# SERPER_API_KEY=your-serper-key (optional, for web search)
# MONGODB_URL=mongodb://host.docker.internal:27017/
```

### First-Time Setup

```bash
# Build the search index (IMPORTANT: Do this first!)
cd websters-package
python scripts/build_index.py
cd ..

# Start development containers with hot reload
docker-compose -f docker-compose.dev.yml up --build
```

### Development Features ✨

- **🔄 Backend Hot Reload**: Python code changes trigger automatic server restart
- **🔥 Frontend Hot Reload**: React/Next.js changes update immediately in browser  
- **📁 Volume Mounting**: Source code mounted directly, no rebuilding needed
- **💾 Persistent Index**: Search index stored in local `index_storage/` directory
- **🐛 Debug Mode**: Full development tools and verbose logging

### Development Commands

```bash
# Start services in development mode
docker-compose -f docker-compose.dev.yml up

# Rebuild and start (after Dockerfile changes)
docker-compose -f docker-compose.dev.yml up --build

# View logs for specific service
docker-compose -f docker-compose.dev.yml logs backend
docker-compose -f docker-compose.dev.yml logs frontend

# Stop all services
docker-compose -f docker-compose.dev.yml down

# Stop and remove volumes/networks
docker-compose -f docker-compose.dev.yml down -v
```

---

## 🏭 Production Setup

### Production Deployment

```bash
# 1. Set up production environment
cp .env.example .env
# Configure production values:
# - Strong JWT_SECRET_KEY
# - Production MongoDB URL
# - API keys

# 2. Build and run production containers
docker-compose up --build -d

# 3. Verify services are running
docker-compose ps
```

### Production Features 🔒

- **🏗️ Optimized Builds**: Multi-stage Docker builds with minimal image size
- **📦 Pre-built Index**: Search index built during container build process
- **🔐 Security**: Production-ready JWT configuration
- **⚡ Performance**: Next.js production build with optimization
- **📊 Health Checks**: Built-in health monitoring endpoints

---

## 🔧 Container Details

### Backend Container (`websters-package/`)

**Production Dockerfile:**
```dockerfile
FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y gcc
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8001
CMD ["python", "main_refactored.py"]
```

**Development Dockerfile.dev:**
- Includes `uvicorn[standard]` for hot reload
- Source code mounted as volume
- Auto-restarts on file changes

### Frontend Container (`chat-interface/`)

**Production Dockerfile:**
```dockerfile
FROM node:20-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build
EXPOSE 3000
CMD ["npm", "start"]
```

**Development Dockerfile.dev:**
- Only installs dependencies in image
- Source code mounted as volume
- Runs `npm run dev` for hot reload

---

## 🌐 Network Configuration

### Service Communication

| Service | Internal Port | External Port | Access |
|---------|--------------|---------------|---------|
| Backend | 8001 | 8001 | `http://localhost:8001` |
| Frontend | 3000 | 3000 | `http://localhost:3000` |
| MongoDB | 27017 | 27017 | `host.docker.internal:27017` |

### Key Network Features:
- **Docker Bridge Network**: Containers communicate using service names
- **Host Access**: `host.docker.internal` allows container → host connections
- **Browser Requests**: Frontend uses `http://localhost:8001` for browser-based API calls

---

## ⚙️ Environment Variables

### Required Variables (.env)

```bash
# OpenAI Configuration (REQUIRED)
OPENAI_API_KEY=sk-your-openai-api-key

# Web Search (OPTIONAL)
SERPER_API_KEY=your-serper-api-key

# MongoDB Configuration
MONGODB_URL=mongodb://host.docker.internal:27017/
DATABASE_NAME=websters_auth

# JWT Security
JWT_SECRET_KEY=your-super-secret-jwt-key-change-in-production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### Frontend Environment
- `NEXT_PUBLIC_API_URL`: Automatically configured in docker-compose
- `NODE_ENV`: Set to `development` in dev mode

---

## 👥 User Management

### Creating Users

```bash
# Method 1: Using Docker container
docker-compose exec backend python scripts/add_user.py username password email@example.com

# Method 2: Local Python (if backend dependencies installed)
cd websters-package
python scripts/add_user.py username password email@example.com
```

### Authentication Flow
1. **Login**: POST to `/login` with username/password → receives JWT token
2. **Authorization**: Include `Authorization: Bearer <token>` in API requests
3. **Frontend**: Token stored in localStorage, managed by AuthContext

---

## 🐳 Docker Commands Reference

### Development Commands

```bash
# Build services
docker-compose -f docker-compose.dev.yml build

# Start in foreground (see logs)
docker-compose -f docker-compose.dev.yml up

# Start in background (detached)
docker-compose -f docker-compose.dev.yml up -d

# View live logs
docker-compose -f docker-compose.dev.yml logs -f

# Restart specific service
docker-compose -f docker-compose.dev.yml restart backend

# Execute commands in running container
docker-compose -f docker-compose.dev.yml exec backend bash
docker-compose -f docker-compose.dev.yml exec frontend sh

# Stop all services
docker-compose -f docker-compose.dev.yml down

# Stop and remove volumes
docker-compose -f docker-compose.dev.yml down -v
```

### Production Commands

```bash
# Build and start production stack
docker-compose up --build -d

# View production logs
docker-compose logs -f

# Scale services (if needed)
docker-compose up -d --scale backend=3

# Update and restart services
docker-compose pull
docker-compose up -d

# Stop production stack
docker-compose down
```

### Individual Container Management

```bash
# Build backend image
cd websters-package
docker build -t websters-backend .

# Build frontend image  
cd chat-interface
docker build -t websters-frontend .

# Run backend standalone
docker run -p 8001:8001 \
  -e OPENAI_API_KEY=your-key \
  -e MONGODB_URL=mongodb://host.docker.internal:27017/ \
  --add-host host.docker.internal:host-gateway \
  websters-backend

# Run frontend standalone
docker run -p 3000:3000 \
  -e NEXT_PUBLIC_API_URL=http://localhost:8001 \
  websters-frontend
```

---

## 🔍 Troubleshooting Guide

### Common Issues & Solutions

**1. MongoDB Connection Failed**
```bash
# Check if MongoDB is running locally
brew services list | grep mongodb
# or
sudo systemctl status mongodb

# Verify connection from container
docker-compose exec backend python -c "
import pymongo
client = pymongo.MongoClient('mongodb://host.docker.internal:27017/')
print('MongoDB connected:', client.admin.command('ismaster'))
"
```

**2. OpenAI API Key Issues**
```bash
# Verify environment variable is set
docker-compose exec backend env | grep OPENAI

# Test API key
docker-compose exec backend python -c "
import os
print('API Key set:', bool(os.getenv('OPENAI_API_KEY')))
"
```

**3. Index Build Failures**
```bash
# Rebuild index manually
docker-compose exec backend python scripts/build_index.py

# Check index files
docker-compose exec backend ls -la index_storage/
```

**4. Port Conflicts**
```bash
# Check what's using ports 3000/8001
lsof -i :3000
lsof -i :8001

# Use different ports in docker-compose.yml
ports:
  - "3001:3000"  # Frontend on 3001
  - "8002:8001"  # Backend on 8002
```

**5. Hot Reload Not Working**
```bash
# Check volume mounts
docker-compose -f docker-compose.dev.yml config

# Verify file permissions (macOS/Linux)
ls -la websters-package/
ls -la chat-interface/
```

---

## 🚀 Deployment Strategies

### AWS ECS Deployment

```bash
# Build and push to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 123456789.dkr.ecr.us-east-1.amazonaws.com

docker build -t websters-backend ./websters-package
docker tag websters-backend:latest 123456789.dkr.ecr.us-east-1.amazonaws.com/websters-backend:latest
docker push 123456789.dkr.ecr.us-east-1.amazonaws.com/websters-backend:latest

docker build -t websters-frontend ./chat-interface  
docker tag websters-frontend:latest 123456789.dkr.ecr.us-east-1.amazonaws.com/websters-frontend:latest
docker push 123456789.dkr.ecr.us-east-1.amazonaws.com/websters-frontend:latest
```

### Kubernetes Deployment

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: websters-config
data:
  NEXT_PUBLIC_API_URL: "http://backend-service.websters.svc.cluster.local:8001"
  MONGODB_URL: "mongodb://mongodb-service.websters.svc.cluster.local:27017/"
```

### Environment-Specific Configuration

**Development:**
- Use `docker-compose.dev.yml`
- Volume mounts for live code changes
- Debug logging enabled
- Local MongoDB connection

**Staging:**  
- Use production Dockerfiles
- Environment-specific .env file
- Staging database connections
- Load balancer testing

**Production:**
- Optimized container images
- Secure JWT secrets  
- Production MongoDB cluster
- Health check monitoring
- Auto-scaling configuration

---

## 📋 Quick Reference Commands

### Daily Development Workflow
```bash
# Start development environment
docker-compose -f docker-compose.dev.yml up -d

# View logs in real-time
docker-compose -f docker-compose.dev.yml logs -f

# Add new user
docker-compose exec backend python scripts/add_user.py newuser password123

# Rebuild index after data changes
docker-compose exec backend python scripts/build_index.py

# Stop development environment
docker-compose -f docker-compose.dev.yml down
```

### Production Deployment
```bash
# Deploy production stack
docker-compose up --build -d

# Monitor health
curl http://localhost:8001/health
curl http://localhost:3000

# View production logs
docker-compose logs -f backend frontend

# Graceful shutdown
docker-compose down
```

This comprehensive setup provides a robust, scalable Docker environment for both development and production deployments of your Webster's RAG system!