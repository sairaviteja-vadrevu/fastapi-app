"""Movies API Routes"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from bson import ObjectId
from helpers.db import get_database

router = APIRouter()

db = get_database("sample_mflix")


class Movie(BaseModel):
    """Movie Model"""

    id: str = Field(alias="_id")
    title: str
    directors: Optional[List[str]]
    year: Optional[int]
    genres: Optional[List[str]]
    cast: Optional[List[str]]


@router.get("/movies", response_model=List[Movie])
async def get_movies():
    """Get all movies"""
    cursor = db.movies.find(
        {}, {"_id": 1, "title": 1, "directors": 1, "year": 1, "genres": 1, "cast": 1}
    ).limit(100)

    movies = []
    async for doc in cursor:
        doc["_id"] = str(doc["_id"])  # Convert ObjectId to string
        movies.append(doc)

    return movies


@router.get("/movies/{movie_id}", response_model=Movie)
async def get_movie(movie_id: str):
    """Get a movie by ID"""
    object_id = ObjectId(movie_id)
    movie = await db.movies.find_one(
        {"_id": object_id},
        {"_id": 1, "title": 1, "directors": 1, "year": 1, "genres": 1, "cast": 1},
    )

    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")

    movie["_id"] = str(movie["_id"])  # Convert ObjectId to string for Pydantic
    return movie
