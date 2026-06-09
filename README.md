# MovieMatch - Movie Recommendation System

A full-stack movie recommendation application built with FastAPI (backend), React (frontend), and PostgreSQL (database).

## 🚀 Quick Start with Docker

### Prerequisites
- [Docker](https://www.docker.com/products/docker-desktop)
- [Docker Compose](https://docs.docker.com/compose/install/)

Works on:
- ✅ Windows (Docker Desktop)
- ✅ macOS (Docker Desktop)
- ✅ Linux (Docker + Docker Compose)
- ✅ CachyOS and other Linux distributions

### One-Command Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-username/MovieMatch.git
   cd MovieMatch
   ```

2. **Start all services:**
   ```bash
   docker compose up
   ```

3. **Wait for "Application startup complete"** in the logs, then open:
   ```
   http://localhost:3000
   ```

**That's it!** Everything is containerized and will work identically on any machine with Docker.

### Stopping Services

```bash
docker compose down          # Stop containers
docker compose down -v       # Stop and remove volumes (clears database)
```

### Services After Running

| Service | URL | Purpose |
|---------|-----|---------|
| Frontend | http://localhost:3000 | React web application |
| Backend API | http://localhost:8000 | FastAPI REST API |
| Backend Docs | http://localhost:8000/docs | Swagger API documentation |
| Database | localhost:5432 | PostgreSQL (user: postgres, password: password) |

## 📁 Project Structure

```
MovieMatch/
├── backend/              # FastAPI application
│   ├── main.py          # Main application entry
│   ├── database.py       # Database configuration
│   ├── models.py         # SQLAlchemy models
│   ├── auth.py           # Authentication logic
│   ├── recommender.py    # Recommendation engine
│   ├── predict.py        # Prediction logic
│   ├── requirements.txt   # Python dependencies
│   └── Dockerfile        # Backend Docker image
├── frontend/             # React application
│   ├── src/              # React components
│   ├── package.json      # Node dependencies
│   └── Dockerfile        # Frontend Docker image
├── docker-compose.yml    # Docker services orchestration
└── README.md             # This file
```

## 🛠️ Development

### Local Development (without Docker)

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

**Database:**
Ensure PostgreSQL is running locally at `localhost:5432` with:
- Username: `postgres`
- Password: `password`
- Database: `moviematch`

## 🐳 Docker Commands

```bash
# Start all services
docker compose up

# Start in background
docker compose up -d

# Stop all services
docker compose down

# View logs
docker compose logs -f

# View logs for specific service
docker compose logs -f backend
docker compose logs -f frontend

# Rebuild images
docker compose up --build

# Remove volumes (resets database)
docker compose down -v
```

## 🔧 Configuration

### Environment Variables

The application uses the following environment variables:

**Backend (.env):**
```
DATABASE_URL=postgresql://postgres:password@db:5432/moviematch
SECRET_KEY=your_secret_key_here
```

**Frontend (.env):**
```
VITE_API_URL=http://localhost:8000
```

## 📝 Notes

- PostgreSQL data is persisted in a Docker volume (`postgres_data`) and survives container restarts
- To reset the database, run: `docker compose down -v`
- Backend automatically reloads on code changes (development mode)
- For production, modify the `docker-compose.yml` to remove `--reload` flag and use proper SECRET_KEY

## 🐛 Troubleshooting

**Tables not created / "relation does not exist" errors:**
```bash
# Restart with clean database
docker compose down -v
docker compose up
```

**Port already in use:**
```bash
# Find process using port (macOS/Linux)
lsof -i :3000      # Frontend
lsof -i :8000      # Backend
lsof -i :5432      # Database

# Change ports in docker-compose.yml if needed
```

**Database connection errors:**
```bash
# Check database logs
docker compose logs db

# Check backend logs
docker compose logs backend

# Restart all services
docker compose down
docker compose up
```

**Frontend can't reach backend:**
- Ensure `VITE_API_URL=http://localhost:8000` (from frontend container perspective)
- Verify backend is responding: `http://localhost:8000/docs`
- Check CORS settings in backend/main.py

**Linux/CachyOS specific:**
- Make sure Docker daemon is running: `sudo systemctl start docker`
- If permission denied, add user to docker group: `sudo usermod -aG docker $USER`
- Then restart Docker: `sudo systemctl restart docker`

## 🔄 Deployment to GitHub

### Step 1: Create GitHub Repository

1. Go to [GitHub](https://github.com/new)
2. Create a new repository named `MovieMatch`
3. **Don't** initialize with README (we already have one)

### Step 2: Push from Command Line

```bash
cd c:\Files\Facultate\LICENTA\MovieMatch

# Configure git (if first time)
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"

# Add remote and push
git remote add origin https://github.com/YOUR-USERNAME/MovieMatch.git
git branch -M main
git push -u origin main
```

### Step 3: Clone and Run on Any Machine

**On CachyOS or any Linux machine:**

```bash
# Clone
git clone https://github.com/YOUR-USERNAME/MovieMatch.git
cd MovieMatch

# Ensure Docker is installed and running
sudo systemctl start docker

# Run
docker compose up
```

Then visit `http://localhost:3000` 

🎉 **Done!** The entire application will work identically on Windows, macOS, Linux, CachyOS, etc.

## 📦 Build for Production

The project is ready for deployment to platforms like:
- Docker registries (Docker Hub, AWS ECR, etc.)
- Kubernetes clusters
- Cloud platforms (AWS ECS, Google Cloud Run, Azure Container Instances, etc.)

Simply push the Docker images after building:
```bash
docker compose build
docker image push your-registry/moviematch-backend:latest
docker image push your-registry/moviematch-frontend:latest
```
