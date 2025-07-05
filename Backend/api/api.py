from fastapi import APIRouter, HTTPException, Depends, status, Header
from pydantic import BaseModel
from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import hashlib
import secrets
import jwt
from datetime import datetime, timedelta
from typing import List, Optional

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

@router.post("/register")
def register(user: UserCreate, db: Session = Depends(get_db)):
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
    user_obj = db.query(User).filter(User.username == user.username).first()
    if not user_obj:
        raise HTTPException(status_code=400, detail="Invalid username or password")
    password_hash = hashlib.sha256(user.password.encode()).hexdigest()
    if user_obj.password_hash != password_hash:
        raise HTTPException(status_code=400, detail="Invalid username or password")
    # Generate JWT access token
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
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
def create_challenge(challenge: ChallengeSchema, db: Session = Depends(get_db), authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    token = authorization.split(" ", 1)[1]
    try:
        jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")
    db_chal = Challenge(
        name=challenge.name,
        description=challenge.description,
        type=challenge.type,
        file_path=challenge.file_path,
        flag=challenge.flag
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
        jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")
    chal = db.query(Challenge).filter(Challenge.id == challenge_id).first()
    if not chal:
        raise HTTPException(status_code=404, detail="Challenge not found")
    if chal.flag == submission.flag:
        return {"msg": "Correct!"}
    else:
        raise HTTPException(status_code=400, detail="Incorrect flag.")
