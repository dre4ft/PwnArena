# PwnArena

PwnArena is a SaaS platform for hosting and playing Capture The Flag (CTF) competitions locally. It allows users to register, log in, upload and download challenges, and submit flags to climb the leaderboard.

## Features
- User registration and login with JWT authentication
- Dashboard for authenticated users
- Challenge listing with download links
- Flag submission and validation
- SQLite database for user and challenge storage
- FastAPI backend and Bootstrap-based frontend

## Project Structure
```
Backend/
  main.py           # FastAPI app entry point
  api/
    api.py          # API endpoints for users and challenges
Frontend/
  index.html        # Landing page (login/register)
  dashboard.html    # Main dashboard for logged-in users
  static/
    index.js        # JS for login/register
    dashboard.js    # JS for dashboard logic
    style.css       # Custom styles
requirements.txt    # Python dependencies
Dockerfile          # (Optional) For containerization
```

## How It Works
- **Landing page**: Users can register or log in.
- **Dashboard**: After login, users see all challenges, can download files, and submit flags.
- **API**: All challenge and flag endpoints require a valid JWT.

## Running Locally
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Start the server:
   ```bash
   cd Backend
   python main.py
   ```
3. Open your browser at [http://localhost:8080](http://localhost:8080)

## API Endpoints
- `POST /api/register` — Register a new user
- `POST /api/login` — Log in and receive a JWT
- `GET /api/challenges` — List all challenges (auth required)
- `POST /api/challenges` — Add a new challenge (auth required)
- `POST /api/challenges/{id}/submit` — Submit a flag for a challenge (auth required)

## Security Notes
- JWT secret key should be changed in production.
- File uploads and user input should be sanitized for production use.

## License
MIT
