"""Insta Scraper API"""

import os
from fastapi import APIRouter, HTTPException
import requests
from dotenv import load_dotenv
from helpers.db import get_database

load_dotenv()

router = APIRouter()

RAPID_API_KEY = os.getenv("RAPID_API_KEY")

db = get_database("insta_scraper")


@router.get("/users/add/{username}", response_model=dict)
async def add_user_to_db(username: str):
    """Add user data to the database by username."""
    try:
        if not RAPID_API_KEY:
            raise HTTPException(
                status_code=500,
                detail="RAPID_API_KEY is not set in the environment variables.",
            )

        user_data = await db.users.find_one({"username": username})

        if user_data:
            return {
                "username": username,
                "message": "User data already exists in the database.",
            }

        url = "https://instagram-scrapper-posts-reels-stories-downloader.p.rapidapi.com/profile_by_username"

        querystring = {"username": username}

        headers = {
            "x-rapidapi-key": RAPID_API_KEY,
            "x-rapidapi-host": "instagram-scrapper-posts-reels-stories-downloader.p.rapidapi.com",
        }

        response = requests.get(url, headers=headers, params=querystring, timeout=60000)

        api_data = response.json()

        # Insert or update user data in MongoDB

        await db.users.insert_one(api_data)

        return {
            "usename": username,
            "message": "User data retrieved successfully",
        }

    except requests.RequestException as e:
        return {
            "username": username,
            "message": f"Error retrieving user data: {str(e)}",
            "status_code": 500,
        }


@router.get("/users/{username}", response_model=dict)
async def get_user(username: str):
    """Get User Data from the database by username."""
    try:
        user_data = await db.users.find_one({"username": username})

        if not user_data:
            raise HTTPException(status_code=404, detail="User not found")

        # Convert _id to string for JSON serialization
        user_data["_id"] = str(user_data["_id"])

        return user_data
    except requests.RequestException as e:
        return {
            "username": username,
            "message": f"Error retrieving user data: {str(e)}",
            "status_code": 500,
        }
