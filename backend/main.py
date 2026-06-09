import time
import logging
from fastapi import FastAPI, Depends, HTTPException, Request, status, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import or_
from sqlalchemy.orm import Session
from database import engine, Base, get_db
from models import Movie, Rating, User, UserUpdate  # Import models to register them with Base
from recommender import Recommender
from predict import RatingPredictor
from auth import (
    oauth2_scheme, create_access_token, get_password_hash,
    verify_password, get_current_user
)
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timedelta
from jose import jwt, JWTError
from dotenv import load_dotenv
import os
from functools import lru_cache
from utils import extract_features

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")


# --- FastAPI app setup ---
app = FastAPI()
logger = logging.getLogger("uvicorn")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://frontend:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Pydantic models ---
class UserCreate(BaseModel):
    email: str
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class MovieResponse(BaseModel):
    id: int
    title: str
    titleType: str
    startYear: int | None
    endYear: int | None
    totalEpisodes: int | None
    genres: str | None
    runtimeMinutes: int | None
    numVotes: int
    averageRating: float
    writers: str | None = None        
    directors: str | None = None      
    userRating: float | None = None
    predictedRating: float | None = None

    class Config:
        from_attributes = True

class RatingCreate(BaseModel):
    movie_id: int
    rating: float

class SearchQuery(BaseModel):
    title: Optional[str] = None
    genres: Optional[str] = None
    writers: Optional[str] = None
    directors: Optional[str] = None
    sort_by: Optional[str] = "averageRating"
    sort_order: Optional[str] = "desc"

class RatingUpdate(BaseModel):
    rating: float

# --- Utility functions ---
def create_access_token(data: dict):
    expire = datetime.utcnow() + timedelta(minutes=30)
    to_encode = data.copy()
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm="HS256")

# --- Startup event ---
@app.on_event("startup")
async def startup_event():
    print(f"{time.strftime('%H:%M:%S')} - Starting startup event...")
    try:
        Base.metadata.create_all(bind=engine)
        print(f"{time.strftime('%H:%M:%S')} - Database tables created")
    except Exception as e:
        print(f"{time.strftime('%H:%M:%S')} - Error creating tables: {e}")
        import time as time_module
        time_module.sleep(2)
        Base.metadata.create_all(bind=engine)
        print(f"{time.strftime('%H:%M:%S')} - Database tables created (retry)")
    
    try:
        db = next(get_db())
        load_imdb_data(db)
        print(f"{time.strftime('%H:%M:%S')} - IMDb data loaded")
    except Exception as e:
        print(f"{time.strftime('%H:%M:%S')} - Warning: Could not load IMDb data: {e}")
    
    try:
        global recommender, rating_predictor
        recommender = Recommender(db)
        recommender.load()
        rating_predictor = RatingPredictor(model_dir="models")
        rating_predictor.load()
        print(f"{time.strftime('%H:%M:%S')} - Recommender and RatingPredictor initialized")
        logger.info(f"Recommender initialized: {recommender is not None}")
    except Exception as e:
        print(f"{time.strftime('%H:%M:%S')} - Warning: Could not initialize models: {e}")
        logger.warning(f"Model initialization failed: {e}")

def load_imdb_data(db: Session):
    if db.query(Movie).count() == 0:
        print(f"{time.strftime('%H:%M:%S')} - Loading movies from datasets/imdb.csv...")
        import pandas as pd
        df = pd.read_csv("datasets/imdb.csv")
        print(f"{time.strftime('%H:%M:%S')} - Number of movies to load: {len(df)}")
        for i, row in df.iterrows():
            if i % 1000 == 0:
                print(f"{time.strftime('%H:%M:%S')} - Loaded {i} movies...")
            movie = Movie(
                id=row["id"],
                titleType=row["titleType"],
                title=row["title"],
                startYear=row["startYear"],
                endYear=row["endYear"] if pd.notna(row["endYear"]) else None,
                runtimeMinutes=row["runtimeMinutes"] if pd.notna(row["runtimeMinutes"]) else None,
                genres=row["genres"],
                totalEpisodes=row["totalEpisodes"] if pd.notna(row["totalEpisodes"]) else None,
                directors=row["directors"],
                writers=row["writers"],
                averageRating=row["averageRating"],
                numVotes=row["numVotes"]
            )
            db.add(movie)
        db.commit()
        print(f"{time.strftime('%H:%M:%S')} - Movies loaded successfully")

@app.middleware("http")
async def log_request(request: Request, call_next):
    response = await call_next(request)
    logger.info(f"Request: {request.method} {request.url} - Status: {response.status_code}")
    logger.info(f"Response headers: {dict(response.headers)}")
    return response

# --- Auth endpoints ---
@app.post("/register", response_model=Token)
async def register(user: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.username == user.username).first():
        raise HTTPException(status_code=400, detail="Username already registered")
    if db.query(User).filter(User.email == user.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_password = get_password_hash(user.password)
    db_user = User(username=user.username, email=user.email, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

# --- Movie endpoints ---
@app.get("/top10", response_model=List[MovieResponse])
async def get_top10(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    movies = db.query(Movie).order_by(Movie.numVotes.desc()).limit(10).all()
    user_ratings = {r.movie_id: r.rating for r in db.query(Rating).filter(Rating.user_id == current_user.id).all()}
    return [
        MovieResponse(
            id=m.id,
            titleType=m.titleType,
            title=m.title,
            startYear=m.startYear,
            endYear=m.endYear,
            runtimeMinutes=m.runtimeMinutes,
            genres=m.genres,
            totalEpisodes=m.totalEpisodes,
            averageRating=m.averageRating,
            numVotes=m.numVotes,
            writers=m.writers,          
            directors=m.directors,       
            userRating=user_ratings.get(m.id),
            predictedRating=None
        ) for m in movies
    ]

@app.post("/predict/{movie_id}", response_model=dict)
async def predict_rating(
    movie_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    movie = db.query(Movie).filter(Movie.id == movie_id).first()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    features = extract_features(movie, recommender.mlb_genres)
    predicted = rating_predictor.predict(movie, recommender.mlb_genres, model="xgb")
    return {"predictedRating": predicted}

@app.post("/rate", response_model=RatingCreate)
async def rate_movie(rating: RatingCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    movie = db.query(Movie).filter(Movie.id == rating.movie_id).first()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    if not (1 <= rating.rating <= 10):
        raise HTTPException(status_code=400, detail="Rating must be between 1 and 10")
    existing_rating = db.query(Rating).filter(
        Rating.user_id == current_user.id, Rating.movie_id == rating.movie_id
    ).first()
    if existing_rating:
        existing_rating.rating = rating.rating
    else:
        db_rating = Rating(user_id=current_user.id, movie_id=rating.movie_id, rating=rating.rating)
        db.add(db_rating)
    db.commit()
    return rating

@app.get("/recommendations", response_model=List[MovieResponse])
async def get_recommendations(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if recommender is None:
        raise HTTPException(status_code=500, detail="Recommender not initialized")
    user_ratings = db.query(Rating).filter(Rating.user_id == current_user.id).all()
    if not user_ratings:
        raise HTTPException(status_code=404, detail="Nothing to recommend! Try rating a few titles.")
    recs = recommender.get_recommendations(current_user.id)
    rec_ids = [rec['id'] for rec in recs]
    movies = db.query(Movie).filter(Movie.id.in_(rec_ids)).all()
    movie_map = {m.id: m for m in movies}
    results = []
    for rec in recs:
        movie = movie_map.get(rec['id'])
        if not movie:
            continue
        results.append(MovieResponse(
            id=movie.id,
            title=movie.title,
            titleType=movie.titleType,
            startYear=movie.startYear,
            endYear=movie.endYear,
            totalEpisodes=movie.totalEpisodes,
            genres=movie.genres,
            runtimeMinutes=movie.runtimeMinutes,
            numVotes=movie.numVotes,
            averageRating=movie.averageRating,
            writers=movie.writers,      
            directors=movie.directors,    
            userRating=None,
            predictedRating=None
        ))
    return results

@app.post("/search", response_model=List[MovieResponse])
async def search_movies(
    query: SearchQuery,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db_query = db.query(Movie)
    if query.title:
        db_query = db_query.filter(Movie.title.ilike(f"%{query.title}%"))
    if query.genres:
        genres = query.genres.split(",")
        conditions = [Movie.genres.ilike(f"%{genre.strip()}%") for genre in genres]
        db_query = db_query.filter(or_(*conditions))
    if query.writers:
        writers = query.writers.split(",")
        conditions = [Movie.writers.ilike(f"%{writer.strip()}%") for writer in writers]
        db_query = db_query.filter(or_(*conditions))
    if query.directors:
        directors = query.directors.split(",")
        conditions = [Movie.directors.ilike(f"%{director.strip()}%") for director in directors]
        db_query = db_query.filter(or_(*conditions))
    if query.sort_by == "averageRating":
        order_column = Movie.averageRating
    elif query.sort_by == "numVotes":
        order_column = Movie.numVotes
    else:
        raise HTTPException(status_code=400, detail="Invalid sort_by parameter. Use 'averageRating' or 'numVotes'.")
    if query.sort_order == "desc":
        db_query = db_query.order_by(order_column.desc())
    elif query.sort_order == "asc":
        db_query = db_query.order_by(order_column.asc())
    else:
        raise HTTPException(status_code=400, detail="Invalid sort_order parameter. Use 'asc' or 'desc'.")
    movies = db_query.all()
    user_ratings = {r.movie_id: r.rating for r in db.query(Rating).filter(Rating.user_id == current_user.id).all()}
    results = []
    for movie in movies:
        results.append(
            MovieResponse(
                id=movie.id,
                title=movie.title,
                titleType=movie.titleType,
                startYear=movie.startYear,
                endYear=movie.endYear,
                totalEpisodes=movie.totalEpisodes,
                genres=movie.genres,
                runtimeMinutes=movie.runtimeMinutes,
                numVotes=movie.numVotes,
                averageRating=movie.averageRating,
                writers=movie.writers,     
                directors=movie.directors,
                userRating=user_ratings.get(movie.id),
                predictedRating=None
            )
        )
    return results

@app.get("/test-cors")
async def test_cors(request: Request):
    logger.info(f"CORS test request from {request.headers.get('origin')}")
    return {"message": "CORS is working"}

@app.get("/genres", response_model=list[str])
async def get_genres(db: Session = Depends(get_db)):
    genres = set()
    for g in db.query(Movie.genres).distinct():
        if g[0]:
            for genre in g[0].split(","):
                genres.add(genre.strip())
    return sorted(genres)

# --- Account endpoints using a router ---
account_router = APIRouter()

@account_router.get("/me")
def get_me(current_user: User = Depends(get_current_user)):
    return {
        "email": current_user.email,
        "username": current_user.username
    }

@account_router.put("/me")
def update_me(
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Verify current password is provided and correct
    if not hasattr(user_update, 'current_password') or not user_update.current_password:
        raise HTTPException(status_code=400, detail="Current password is required")
    
    if not verify_password(user_update.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    
    if user_update.email:
        current_user.email = user_update.email
    if user_update.username:
        current_user.username = user_update.username
    if user_update.password:
        current_user.hashed_password = get_password_hash(user_update.password)
    db.commit()
    db.refresh(current_user)
    return {"msg": "Account updated"}

@account_router.get("/my-ratings")
def get_my_ratings(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    ratings = (
        db.query(Rating)
        .join(Movie, Rating.movie_id == Movie.id)
        .filter(Rating.user_id == current_user.id)
        .all()
    )
    return [
        {
            "rating_id": r.id,  # rating ID
            "movie_id": r.movie.id,
            "title": r.movie.title,
            "titleType": r.movie.titleType,
            "startYear": r.movie.startYear,
            "endYear": r.movie.endYear,
            "totalEpisodes": r.movie.totalEpisodes,
            "genres": r.movie.genres,
            "runtimeMinutes": r.movie.runtimeMinutes,
            "numVotes": r.movie.numVotes,
            "averageRating": r.movie.averageRating,
            "writers": r.movie.writers,
            "directors": r.movie.directors,
            "rating": r.rating
        }
        for r in ratings if r.movie is not None
    ]

@account_router.put("/my-ratings/{rating_id}")
def update_rating(
    rating_id: int,
    rating_update: RatingUpdate,  # pydantic
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    r = db.query(Rating).filter_by(id=rating_id, user_id=current_user.id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Rating not found")
    r.rating = rating_update.rating
    db.commit()
    return {"msg": "Rating updated"}

@account_router.delete("/my-ratings/{rating_id}")
def delete_rating(rating_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    r = db.query(Rating).filter_by(id=rating_id, user_id=current_user.id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Rating not found")
    db.delete(r)
    db.commit()
    return {"msg": "Rating deleted"}

# --- Register the router ---
app.include_router(account_router)

@app.post("/retrain-recommender")
async def retrain_recommender_endpoint(current_user: User = Depends(get_current_user)):
    """
    Retrain the recommender (KMeans and XGBoost) and reload the model in memory.
    """
    global recommender
    recommender.train_model()
    recommender.save()
    recommender.load()
    return {"msg": "Recommender retrained and updated."}