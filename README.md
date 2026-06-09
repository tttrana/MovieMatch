# MovieMatch - Smart Movie Recommendation System

A full-stack movie recommendation application built with FastAPI (backend), React (frontend), and PostgreSQL (database).

## Quick Start with Docker

### Prerequisites
- [Docker](https://www.docker.com/products/docker-desktop)
- [Docker Compose](https://docs.docker.com/compose/install/)

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

## Project Structure

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

## Development

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

## Docker Commands

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

## Configuration

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

## Notes

- PostgreSQL data is persisted in a Docker volume (`postgres_data`) and survives container restarts
- To reset the database, run: `docker compose down -v`
- Backend automatically reloads on code changes (development mode)
- For production, modify the `docker-compose.yml` to remove `--reload` flag and use proper SECRET_KEY

## Troubleshooting

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
