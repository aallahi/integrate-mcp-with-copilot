# Quick Reference Guide

## Running the Application with Docker

### Prerequisites
- Install [Docker Desktop](https://www.docker.com/products/docker-desktop) for Windows

### Commands

| Task | Command |
|------|---------|
| **Run app with Docker** | `docker-compose up --build` |
| **Stop app** | `Ctrl+C` |
| **View app** | `http://localhost:8000/static/index.html` |
| **View API docs** | `http://localhost:8000/docs` |
| **Rebuild image** | `docker-compose up --build` |
| **Remove containers** | `docker-compose down` |

### Step-by-Step Setup

1. **Open PowerShell** in the project directory
2. **Run the app:**
   ```powershell
   docker-compose up --build
   ```
3. **Wait for startup message:**
   ```
   app-1  | INFO:     Uvicorn running on http://0.0.0.0:8000
   ```
4. **Access the application:**
   - Frontend: `http://localhost:8000/static/index.html`
   - API Documentation: `http://localhost:8000/docs`

### Stopping the Application
- Press `Ctrl+C` in the PowerShell terminal

### Removing Containers
```powershell
docker-compose down
```

## What Was Created

### Dockerfile
- Packages the Python app into a container
- Installs FastAPI and uvicorn dependencies
- Exposes port 8000
- Starts the app automatically

### docker-compose.yml
- Simplifies Docker container management
- Enables live reload for development
- Maps port 8000 to your PC
- Reloads Python code changes automatically; rebuild the image after changing dependencies with `docker-compose up --build`

### .dockerignore
- Speeds up Docker builds by excluding unnecessary files
- Prevents __pycache__, .git, and other files from being copied

## Why Docker?

✅ No Python installation needed on your PC  
✅ Works on Windows, Mac, and Linux  
✅ Isolates app dependencies  
✅ Live reload for fast development  
✅ Easy deployment to production  

## Troubleshooting

### Port 8000 already in use
```powershell
# Find process using port 8000
netstat -ano | findstr :8000

# Kill the process (replace PID with the process ID)
taskkill /PID <PID> /F
```

### Docker not found
- Ensure Docker Desktop is installed and running
- Check: `docker --version`

### App not responding
- Check Docker logs: `docker-compose logs -f`
- Verify port 8000 is accessible: `http://localhost:8000/docs`
