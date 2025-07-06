from fastapi import APIRouter, HTTPException, Depends, status, Header, UploadFile, File, Form
from pydantic import BaseModel
from sqlalchemy import Column, Integer, String, create_engine, ForeignKey, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import hashlib
import secrets
import jwt
from datetime import datetime, timedelta
from typing import List, Optional
import shutil
import os
from fastapi.responses import FileResponse
import re

DATABASE_URL = "sqlite:///./users.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password_hash = Column(String)

class Challenge(Base):
    __tablename__ = 'challenges'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String)
    type = Column(String)
    file_path = Column(String)
    flag = Column(String, unique=True)

class ChallengeSolve(Base):
    __tablename__ = 'challenge_solves'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    challenge_id = Column(Integer, ForeignKey('challenges.id'))
    __table_args__ = (UniqueConstraint('user_id', 'challenge_id', name='_user_challenge_uc'),)

Base.metadata.create_all(bind=engine)

class UserCreate(BaseModel):
    username: str
    password: str

class ChallengeSchema(BaseModel):
    id: Optional[int]
    name: str
    description: str
    type: str
    file_path: str
    # flag is not exposed in API
    class Config:
        orm_mode = True

router = APIRouter()

SECRET_KEY = "your-secret-key"  # Change this to a secure random value in production
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

USERNAME_REGEX = re.compile(r'^[a-zA-Z0-9_]{3,32}$')
PASSWORD_MIN_LENGTH = 8
CHALLENGE_NAME_MAX = 64
CHALLENGE_TYPE_MAX = 32
CHALLENGE_DESC_MAX = 512
FLAG_MAX = 128
DESCRIPTION_SAFE_REGEX = re.compile(r'^[^<>]*$')


def check_jwt(token: str):
    try:
        jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return True
    except jwt.ExpiredSignatureError:
        return False
    except jwt.InvalidTokenError:
        return False
        
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def sanitize_text(text, max_length):
    text = text.strip()
    if len(text) > max_length:
        raise HTTPException(status_code=400, detail="Input too long.")
    return text

@router.post("/register")
def register(user: UserCreate, db: Session = Depends(get_db)):
    # Username validation
    if not USERNAME_REGEX.match(user.username):
        raise HTTPException(status_code=400, detail="Username must be 3-32 characters, alphanumeric or underscore.")
    # Password validation
    if len(user.password) < PASSWORD_MIN_LENGTH:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters.")
    user_obj = db.query(User).filter(User.username == user.username).first()
    if user_obj:
        raise HTTPException(status_code=400, detail="Username already registered")
    password_hash = hashlib.sha256(user.password.encode()).hexdigest()
    new_user = User(username=user.username, password_hash=password_hash)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"msg": "User registered successfully"}

@router.post("/login")
def login(user: UserCreate, db: Session = Depends(get_db)):
    # Username validation (generic error for security)
    if not USERNAME_REGEX.match(user.username):
        raise HTTPException(status_code=400, detail="Invalid username or password")
    if len(user.password) < PASSWORD_MIN_LENGTH:
        raise HTTPException(status_code=400, detail="Invalid username or password")
    user_obj = db.query(User).filter(User.username == user.username).first()
    if not user_obj:
        raise HTTPException(status_code=400, detail="Invalid username or password")
    password_hash = hashlib.sha256(user.password.encode()).hexdigest()
    if user_obj.password_hash != password_hash:
        raise HTTPException(status_code=400, detail="Invalid username or password")
    # Generate JWT access token
    expire = datetime.now() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": str(user_obj.id),
        "username": user_obj.username,
        "exp": expire
    }
    access_token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return {
        "msg": "Login successful",
        "user": {
            "id": user_obj.id,
            "username": user_obj.username
        },
        "access_token": access_token
    }

@router.get("/challenges", response_model=List[ChallengeSchema])
def get_challenges(db: Session = Depends(get_db), authorization: str = Header(None)):
    # JWT validation (simple, not production ready)
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    token = authorization.split(" ", 1)[1]
    try:
        jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")
    challenges = db.query(Challenge).all()
    return challenges

@router.post("/challenges", response_model=ChallengeSchema)
def create_challenge(
    name: str = Form(...),
    description: str = Form(...),
    type: str = Form(...),
    flag: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    authorization: str = Header(None)
):
    # Sanitize and validate challenge fields
    name = sanitize_text(name, CHALLENGE_NAME_MAX)
    type = sanitize_text(type, CHALLENGE_TYPE_MAX)
    description = sanitize_text(description, CHALLENGE_DESC_MAX)
    flag = sanitize_text(flag, FLAG_MAX)
    # Prevent XSS in description
    if not DESCRIPTION_SAFE_REGEX.match(description):
        raise HTTPException(status_code=400, detail="Description contains forbidden characters (no HTML tags allowed).")
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    token = authorization.split(" ", 1)[1]
    try:
        jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")
    # Validate file type and MIME type
    allowed = False
    filename = file.filename.lower()
    content_type = file.content_type
    if filename == "dockerfile" and content_type in ["text/plain", "application/octet-stream"]:
        allowed = True
    elif filename.endswith(".zip") and content_type in ["application/zip", "application/x-zip-compressed", "multipart/x-zip"]:
        allowed = True
    elif filename in ["docker-compose.yml", "docker-compose.yaml"] and content_type in ["text/yaml", "application/x-yaml", "text/plain", "application/octet-stream"]:
        allowed = True
    if not allowed:
        # Read and shred the file
        try:
            while file.file.read(4096):
                pass  # Read and discard
        except Exception:
            pass
        raise HTTPException(status_code=400, detail="File must be a Dockerfile, docker-compose file, or zip archive (with correct MIME type).")
    # Save file with timestamp
    os.makedirs("challenges", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    save_filename = f"{name}_{timestamp}_{file.filename}"
    file_path = os.path.join("challenges", save_filename)
    with open(file_path, "wb") as buffer:
        file.file.seek(0)
        shutil.copyfileobj(file.file, buffer)
    db_chal = Challenge(
        name=name,
        description=description,
        type=type,
        file_path=file_path,
        flag=flag
    )
    db.add(db_chal)
    db.commit()
    db.refresh(db_chal)
    return db_chal

class FlagSubmission(BaseModel):
    flag: str

@router.post("/challenges/{challenge_id}/submit")
def submit_flag(challenge_id: int, submission: FlagSubmission, db: Session = Depends(get_db), authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    token = authorization.split(" ", 1)[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")
    chal = db.query(Challenge).filter(Challenge.id == challenge_id).first()
    if not chal:
        raise HTTPException(status_code=404, detail="Challenge not found")
    if chal.flag == submission.flag:
        user_id = int(payload["sub"])
        # Check if already solved
        existing = db.query(ChallengeSolve).filter_by(user_id=user_id, challenge_id=challenge_id).first()
        if not existing:
            solve = ChallengeSolve(user_id=user_id, challenge_id=challenge_id)
            db.add(solve)
            db.commit()
        return {"msg": "Correct!"}
    else:
        raise HTTPException(status_code=400, detail="Incorrect flag.")

@router.get("/challenges/{challenge_id}/download")
def download_challenge_file(challenge_id: int, db: Session = Depends(get_db), authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    token = authorization.split(" ", 1)[1]
    try:
        jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")
    chal = db.query(Challenge).filter(Challenge.id == challenge_id).first()
    if not chal:
        raise HTTPException(status_code=404, detail="Challenge not found")
    if not os.path.exists(chal.file_path):
        raise HTTPException(status_code=404, detail="File not found")
    filename = os.path.basename(chal.file_path)
    return FileResponse(chal.file_path, filename=filename, media_type='application/octet-stream')

@router.get("/leaderboard")
def get_leaderboard(db: Session = Depends(get_db)):
    from sqlalchemy import func
    results = db.query(User.username, func.count(ChallengeSolve.challenge_id).label('solves')) \
        .join(ChallengeSolve, User.id == ChallengeSolve.user_id) \
        .group_by(User.id) \
        .order_by(func.count(ChallengeSolve.challenge_id).desc(), User.username.asc()) \
        .all()
    leaderboard = [{"username": r[0], "solves": r[1]} for r in results]
    return leaderboard
