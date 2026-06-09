from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from typing import Optional
from pydantic import EmailStr, BaseModel
from database import Base

class Movie(Base):
    __tablename__ = "movies"

    id = Column(Integer, primary_key=True, index=True)
    titleType = Column(String)
    title = Column(String)
    startYear = Column(Integer)
    endYear = Column(Integer, nullable=True)
    runtimeMinutes = Column(Integer, nullable=True)
    genres = Column(String)
    totalEpisodes = Column(Integer, nullable=True)
    directors = Column(String)
    writers = Column(String)
    averageRating = Column(Float)
    numVotes = Column(Integer)

    ratings = relationship("Rating", back_populates="movie")

class Rating(Base):
    __tablename__ = "ratings"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    movie_id = Column(Integer, ForeignKey("movies.id"), index=True)
    rating = Column(Float)

    user = relationship("User", back_populates="ratings")
    movie = relationship("Movie", back_populates="ratings")

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)

    ratings = relationship("Rating", back_populates="user")

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    password: Optional[str] = None
    current_password: Optional[str] = None