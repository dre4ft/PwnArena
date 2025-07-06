# PwnArena

PwnArena is a modern SaaS platform for hosting and playing Capture The Flag (CTF) competitions. Built with FastAPI (Python) and a Bootstrap-powered frontend, it enables secure challenge management, user authentication, and real-time leaderboards—all containerized for easy deployment.

## Features
- User registration and login with JWT authentication
- Secure dashboard for authenticated users
- Upload/download challenges (Dockerfile, docker-compose, or zip only)
- Challenge flag submission and validation
- Real-time leaderboard
- SQLite database for persistent storage
- FastAPI backend, Bootstrap/HTML/JS frontend
- Docker-ready for local or cloud deployment

## Project Structure
```
Backend/
  main.py           # FastAPI app entry point
  api/
    api.py          # API endpoints (users, challenges, leaderboard)
Frontend/
  index.html        # Landing page (login/register)
  dashboard.html    # Main dashboard (challenges, upload, flag submit)
  leaderboard.html  # Leaderboard page
  static/
    index.js        # JS for login/register
    dashboard.js    # JS for dashboard logic
    leaderboard.js  # JS for leaderboard
    style.css       # Custom styles
requirements.txt    # Python dependencies
Dockerfile          # Containerization
```

## How It Works
- **Landing page**: Register or log in to get started.
- **Dashboard**: View/upload/download challenges, submit flags, and see your progress.
- **Leaderboard**: See top solvers and your rank.
- **API**: All challenge and flag endpoints require a valid JWT (handled automatically by the frontend).

## Allowed Challenge File Formats
- `Dockerfile`
- `docker-compose.yml` or `docker-compose.yaml`
- `.zip` archive

Uploads of other file types are rejected for security.

## Running Locally
1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
2. **Start the server:**
   ```bash
   cd Backend
   python main.py
   ```
3. **Open your browser:**
   [http://localhost:8080](http://localhost:8080)

## Docker Usage
1. **Build the image:**
   ```bash
   podman build -t pwna-arena .
   # or
   docker build -t pwna-arena .
   ```
2. **Run the container:**
   ```bash
   podman run -p 8080:8080 pwna-arena
   # or
   docker run -p 8080:8080 pwna-arena
   ```

## API Endpoints (all require JWT unless noted)
- `POST /api/register` — Register a new user
- `POST /api/login` — Log in and receive a JWT
- `GET /api/challenges` — List all challenges
- `POST /api/challenges` — Add a new challenge (file upload)
- `POST /api/challenges/{id}/submit` — Submit a flag for a challenge
- `GET /api/challenges/{id}/download` — Download a challenge file
- `GET /api/leaderboard` — Get leaderboard data

## Security Notes
- Change the `SECRET_KEY` in production.
- Only Dockerfile, docker-compose, or zip files are accepted for uploads.
- JWT is required for all sensitive endpoints.
- User input and file uploads are validated on both frontend and backend.

## License
MIT
